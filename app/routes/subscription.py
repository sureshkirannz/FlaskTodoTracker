import json
import os
import stripe
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Organization, Subscription
from app.utils import admin_required

subscription = Blueprint('subscription', __name__, url_prefix='/subscription')

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Define subscription plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price_monthly': 0,
        'price_id_monthly': None,
        'price_yearly': 0,
        'price_id_yearly': None,
        'features': [
            'Up to 50 visitors per month',
            'Basic visitor check-in',
            'Email notifications',
            '1 staff account'
        ],
        'limits': {
            'visitors_per_month': 50,
            'staff_accounts': 1,
            'badge_printing': False,
            'document_signing': False,
            'visitor_photo': True,
            'preregister': False,
            'analytics': False
        }
    },
    'starter': {
        'name': 'Starter',
        'price_monthly': 29,
        'price_id_monthly': 'price_starter_monthly', # Replace with actual Stripe price ID
        'price_yearly': 290,
        'price_id_yearly': 'price_starter_yearly', # Replace with actual Stripe price ID
        'features': [
            'Up to 200 visitors per month',
            'Visitor photo capture',
            'Badge printing',
            '5 staff accounts',
            'Basic analytics'
        ],
        'limits': {
            'visitors_per_month': 200,
            'staff_accounts': 5,
            'badge_printing': True,
            'document_signing': False,
            'visitor_photo': True,
            'preregister': True,
            'analytics': True
        }
    },
    'professional': {
        'name': 'Professional',
        'price_monthly': 99,
        'price_id_monthly': 'price_professional_monthly', # Replace with actual Stripe price ID
        'price_yearly': 990,
        'price_id_yearly': 'price_professional_yearly', # Replace with actual Stripe price ID
        'features': [
            'Unlimited visitors',
            'Document signing',
            'Custom badge templates',
            'Unlimited staff accounts',
            'Advanced analytics and reports',
            'Visitor pre-registration',
            'Priority support'
        ],
        'limits': {
            'visitors_per_month': 100000, # Effectively unlimited
            'staff_accounts': 100000, # Effectively unlimited
            'badge_printing': True,
            'document_signing': True,
            'visitor_photo': True,
            'preregister': True,
            'analytics': True
        }
    }
}

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
    
    return render_template('subscription/index.html', 
                          title='Subscription',
                          plans=SUBSCRIPTION_PLANS,
                          current_plan=current_plan,
                          subscription_history=subscription_history,
                          organization=organization)

@subscription.route('/plans')
@login_required
@admin_required
def plans():
    """View available subscription plans"""
    organization = Organization.query.get(current_user.organization_id)
    current_plan = organization.subscription_plan
    
    return render_template('subscription/plans.html', 
                          title='Subscription Plans',
                          plans=SUBSCRIPTION_PLANS,
                          current_plan=current_plan)

@subscription.route('/checkout/<plan_id>/<billing_cycle>')
@login_required
@admin_required
def checkout(plan_id, billing_cycle):
    """Redirect to Stripe checkout for subscription"""
    organization = Organization.query.get(current_user.organization_id)
    
    if plan_id not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan', 'danger')
        return redirect(url_for('subscription.plans'))
    
    if billing_cycle not in ['monthly', 'yearly']:
        flash('Invalid billing cycle', 'danger')
        return redirect(url_for('subscription.plans'))
    
    # Get the price ID based on the plan and billing cycle
    price_id = SUBSCRIPTION_PLANS[plan_id].get(f'price_id_{billing_cycle}')
    
    if not price_id:
        flash('This plan is not available for the selected billing cycle', 'danger')
        return redirect(url_for('subscription.plans'))
    
    # Determine success and cancel URLs
    success_url = url_for('subscription.success', _external=True)
    cancel_url = url_for('subscription.plans', _external=True)
    
    try:
        # Create or retrieve Stripe customer
        if organization.stripe_customer_id:
            customer = stripe.Customer.retrieve(organization.stripe_customer_id)
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=organization.name,
                metadata={
                    'organization_id': organization.id
                }
            )
            # Save the Stripe customer ID to the organization
            organization.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'organization_id': organization.id,
                'plan_id': plan_id,
                'billing_cycle': billing_cycle
            }
        )
        
        # Redirect to Stripe checkout
        return redirect(checkout_session.url)
    
    except stripe.error.StripeError as e:
        flash(f'An error occurred while processing your subscription: {str(e)}', 'danger')
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
        stripe_subscription = subscriptions.data[0]
        stripe.Subscription.delete(stripe_subscription.id)
        
        # Update subscription in the database
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription.id
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
    
    except stripe.error.StripeError as e:
        flash(f'An error occurred while cancelling your subscription: {str(e)}', 'danger')
    
    return redirect(url_for('subscription.index'))

@subscription.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    event = None
    payload = request.data.decode('utf-8')
    signature = request.headers.get('Stripe-Signature')
    
    # Get the webhook secret from environment variables
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': str(e)}), 400
    
    # Handle specific events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Get metadata
        org_id = session.get('metadata', {}).get('organization_id')
        plan_id = session.get('metadata', {}).get('plan_id')
        billing_cycle = session.get('metadata', {}).get('billing_cycle')
        
        if org_id and plan_id:
            handle_successful_checkout(org_id, plan_id, billing_cycle, session)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            handle_invoice_paid(subscription_id)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        if customer_id:
            handle_subscription_cancelled(customer_id, subscription.id)
    
    return jsonify({'status': 'success'})

def handle_successful_checkout(org_id, plan_id, billing_cycle, session):
    """Handle successful checkout event"""
    try:
        # Get organization
        organization = Organization.query.get(int(org_id))
        
        if not organization:
            return
        
        # Get subscription details
        subscription_id = session.get('subscription')
        
        if subscription_id:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Calculate start and end dates
            start_date = datetime.fromtimestamp(stripe_subscription.current_period_start)
            end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            # Update organization
            organization.subscription_plan = plan_id
            organization.subscription_status = 'active'
            organization.subscription_expires_at = end_date
            db.session.commit()
            
            # Create subscription record
            price = SUBSCRIPTION_PLANS[plan_id].get(f'price_{billing_cycle}', 0)
            features_json = json.dumps(SUBSCRIPTION_PLANS[plan_id].get('features', []))
            
            subscription = Subscription(
                organization_id=organization.id,
                plan_name=SUBSCRIPTION_PLANS[plan_id].get('name', plan_id),
                status='active',
                stripe_subscription_id=subscription_id,
                start_date=start_date,
                end_date=end_date,
                price=price,
                features=features_json
            )
            db.session.add(subscription)
            db.session.commit()
    
    except Exception as e:
        print(f"Error handling checkout: {str(e)}")

def handle_invoice_paid(subscription_id):
    """Handle invoice payment success event"""
    try:
        # Get subscription from Stripe
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = stripe_subscription.customer
        
        # Get organization
        organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not organization:
            return
        
        # Update subscription end date
        end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)
        organization.subscription_expires_at = end_date
        organization.subscription_status = 'active'
        db.session.commit()
        
        # Update subscription record
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if subscription:
            subscription.status = 'active'
            subscription.end_date = end_date
            db.session.commit()
    
    except Exception as e:
        print(f"Error handling invoice: {str(e)}")

def handle_subscription_cancelled(customer_id, subscription_id):
    """Handle subscription cancellation event"""
    try:
        # Get organization
        organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not organization:
            return
        
        # Update organization
        organization.subscription_plan = 'free'
        organization.subscription_status = 'cancelled'
        db.session.commit()
        
        # Update subscription record
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.end_date = datetime.utcnow()
            db.session.commit()
    
    except Exception as e:
        print(f"Error handling cancellation: {str(e)}")