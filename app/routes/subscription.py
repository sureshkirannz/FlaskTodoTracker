import json
import os
import stripe
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Organization, Subscription
from app.utils import admin_required
from app.subscription_plans import get_plan, get_all_plans, compare_plans
from app.stripe_utils import create_customer, create_subscription, cancel_subscription, create_checkout_session, handle_webhook_event
from app.forms import SubscriptionPlanForm

subscription = Blueprint('subscription', __name__, url_prefix='/subscription')

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@subscription.route('/')
@login_required
@admin_required
def index():
    """Subscription plans page"""
    organization = Organization.query.get(current_user.organization_id)
    current_plan = organization.subscription_plan
    
    # Get subscription history
    subscription_history = Subscription.query.filter_by(
        organization_id=current_user.organization_id
    ).order_by(
        Subscription.start_date.desc()
    ).all()
    
    # Get plan details
    plans = get_all_plans()
    current_plan_details = get_plan(current_plan)
    
    return render_template('subscription/index.html', 
                          title='Subscription',
                          plans=plans,
                          current_plan=current_plan,
                          current_plan_details=current_plan_details,
                          subscription_history=subscription_history,
                          organization=organization)

@subscription.route('/plans')
@login_required
@admin_required
def plans():
    """View available subscription plans"""
    organization = Organization.query.get(current_user.organization_id)
    current_plan = organization.subscription_plan
    
    # Get plan comparison data
    plan_comparison = compare_plans()
    
    form = SubscriptionPlanForm()
    if current_plan:
        form.plan_id.default = current_plan
    
    return render_template('subscription/plans.html', 
                          title='Subscription Plans',
                          plans=get_all_plans(),
                          plan_comparison=plan_comparison,
                          current_plan=current_plan,
                          form=form)

@subscription.route('/checkout', methods=['POST'])
@login_required
@admin_required
def checkout_form():
    """Process subscription plan form and redirect to checkout"""
    form = SubscriptionPlanForm()
    if form.validate_on_submit():
        return redirect(url_for('subscription.checkout', 
                              plan_id=form.plan_id.data, 
                              billing_cycle=form.billing_cycle.data))
    
    flash('Please select a valid plan and billing cycle', 'danger')
    return redirect(url_for('subscription.plans'))

@subscription.route('/checkout/<plan_id>/<billing_cycle>')
@login_required
@admin_required
def checkout(plan_id, billing_cycle):
    """Redirect to Stripe checkout for subscription"""
    organization = Organization.query.get(current_user.organization_id)
    
    # Validate plan and billing cycle
    plan = get_plan(plan_id)
    if not plan:
        flash('Invalid subscription plan', 'danger')
        return redirect(url_for('subscription.plans'))
    
    if billing_cycle not in ['monthly', 'yearly']:
        flash('Invalid billing cycle', 'danger')
        return redirect(url_for('subscription.plans'))
    
    # Ensure organization has a Stripe customer ID
    if not organization.stripe_customer_id:
        customer_id = create_customer(organization, current_user)
        if customer_id:
            organization.stripe_customer_id = customer_id
            db.session.commit()
        else:
            flash('Error creating payment profile', 'danger')
            return redirect(url_for('subscription.plans'))
    
    # Determine success and cancel URLs
    success_url = url_for('subscription.success', _external=True)
    cancel_url = url_for('subscription.plans', _external=True)
    
    # Create checkout session
    checkout_url = create_checkout_session(
        organization, 
        plan_id, 
        billing_cycle,
        success_url,
        cancel_url
    )
    
    if checkout_url:
        return redirect(checkout_url)
    else:
        flash('Error creating checkout session', 'danger')
        return redirect(url_for('subscription.plans'))

@subscription.route('/success')
@login_required
@admin_required
def success():
    """Subscription success page"""
    return render_template('subscription/success.html', title='Subscription Success')

@subscription.route('/cancel')
@login_required
@admin_required
def cancel():
    """Cancel subscription"""
    organization = Organization.query.get(current_user.organization_id)
    
    if not organization.stripe_customer_id:
        flash('No active subscription found', 'warning')
        return redirect(url_for('subscription.index'))
    
    try:
        # Get customer's subscriptions from Stripe
        subscriptions = stripe.Subscription.list(
            customer=organization.stripe_customer_id,
            status='active',
            limit=1
        )
        
        if not subscriptions.data:
            flash('No active subscription found', 'warning')
            return redirect(url_for('subscription.index'))
        
        # Cancel the subscription
        stripe_subscription_id = subscriptions.data[0].id
        if cancel_subscription(stripe_subscription_id):
            # Update subscription in the database
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=stripe_subscription_id
            ).first()
            
            if subscription:
                subscription.status = 'cancelled'
                subscription.end_date = datetime.utcnow()
                db.session.commit()
            
            # Downgrade organization to free plan after the current period ends
            organization.subscription_plan = 'free'
            organization.subscription_status = 'cancelled'
            db.session.commit()
            
            flash('Your subscription has been cancelled', 'success')
        else:
            flash('An error occurred while cancelling your subscription', 'danger')
    
    except Exception as e:
        flash(f'An error occurred while cancelling your subscription: {str(e)}', 'danger')
    
    return redirect(url_for('subscription.index'))

@subscription.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    signature = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Process the webhook event
    event_data = handle_webhook_event(payload, signature, webhook_secret)
    
    if not event_data:
        return jsonify({'error': 'Invalid webhook event'}), 400
    
    # Process the event based on its type
    event_type = event_data.get('type')
    
    if event_type == 'customer.subscription.created' or event_type == 'customer.subscription.updated':
        # Update organization subscription details
        org_id = event_data.get('organization_id')
        plan_id = event_data.get('plan_id')
        status = event_data.get('status')
        subscription_id = event_data.get('subscription_id')
        
        if org_id and subscription_id:
            # Get details from Stripe
            try:
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                
                # Update organization
                organization = Organization.query.get(int(org_id))
                if organization:
                    organization.subscription_plan = plan_id or organization.subscription_plan
                    organization.subscription_status = status
                    organization.subscription_expires_at = datetime.fromtimestamp(
                        stripe_subscription.current_period_end
                    )
                    db.session.commit()
                    
                    # Create or update subscription record
                    subscription = Subscription.query.filter_by(
                        stripe_subscription_id=subscription_id
                    ).first()
                    
                    if not subscription:
                        # Create new subscription record
                        plan = get_plan(plan_id)
                        price = 0
                        features = []
                        
                        if plan:
                            billing_cycle = stripe_subscription.metadata.get('billing_cycle', 'monthly')
                            price = plan.get(f'price_{billing_cycle}', 0)
                            features = plan.get('features', [])
                        
                        subscription = Subscription(
                            organization_id=organization.id,
                            plan_name=plan.get('name', plan_id) if plan else plan_id,
                            status=status,
                            stripe_subscription_id=subscription_id,
                            start_date=datetime.fromtimestamp(stripe_subscription.current_period_start),
                            end_date=datetime.fromtimestamp(stripe_subscription.current_period_end),
                            price=price,
                            features=json.dumps(features)
                        )
                        db.session.add(subscription)
                    else:
                        # Update existing record
                        subscription.status = status
                        subscription.end_date = datetime.fromtimestamp(
                            stripe_subscription.current_period_end
                        )
                    
                    db.session.commit()
            except Exception as e:
                print(f"Error processing subscription event: {str(e)}")
    
    elif event_type == 'customer.subscription.deleted':
        # Handle subscription cancellation
        customer_id = event_data.get('customer_id')
        subscription_id = event_data.get('subscription_id')
        
        if customer_id and subscription_id:
            try:
                # Update organization
                organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
                if organization:
                    organization.subscription_plan = 'free'
                    organization.subscription_status = 'cancelled'
                    db.session.commit()
                    
                    # Update subscription record
                    subscription = Subscription.query.filter_by(
                        stripe_subscription_id=subscription_id
                    ).first()
                    
                    if subscription:
                        subscription.status = 'cancelled'
                        subscription.end_date = datetime.utcnow()
                        db.session.commit()
            except Exception as e:
                print(f"Error processing subscription deletion: {str(e)}")
    
    return jsonify({'status': 'success'})

