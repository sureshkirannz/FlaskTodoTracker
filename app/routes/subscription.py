import os
import json
import stripe
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from app import db
from app.models import Organization, Subscription
from app.utils import admin_required

subscription = Blueprint('subscription', __name__, url_prefix='/subscription')

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Define subscription plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free Plan',
        'price': 0.00,
        'features': {
            'visitors_per_month': 50,
            'staff_members': 5,
            'email_notifications': True,
            'photo_capture': True,
            'badge_printing': False,
            'reports': 'basic'
        }
    },
    'basic': {
        'name': 'Basic Plan',
        'price': 29.99,
        'features': {
            'visitors_per_month': 200,
            'staff_members': 15,
            'email_notifications': True,
            'photo_capture': True,
            'badge_printing': True,
            'reports': 'standard'
        }
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 79.99,
        'features': {
            'visitors_per_month': 500,
            'staff_members': 50,
            'email_notifications': True,
            'photo_capture': True,
            'badge_printing': True,
            'custom_badges': True,
            'document_signing': True,
            'reports': 'advanced'
        }
    },
    'enterprise': {
        'name': 'Enterprise Plan',
        'price': 199.99,
        'features': {
            'visitors_per_month': 'unlimited',
            'staff_members': 'unlimited',
            'email_notifications': True,
            'photo_capture': True,
            'badge_printing': True,
            'custom_badges': True,
            'document_signing': True,
            'reports': 'advanced',
            'api_access': True,
            'dedicated_support': True
        }
    }
}

@subscription.route('/')
@login_required
@admin_required
def index():
    """Subscription management page"""
    organization = Organization.query.get(current_user.organization_id)
    
    # Get current subscription
    current_subscription = Subscription.query.filter_by(
        organization_id=current_user.organization_id,
        status='active'
    ).first()
    
    return render_template(
        'subscription/index.html',
        title='Subscription Management',
        organization=organization,
        current_subscription=current_subscription,
        plans=SUBSCRIPTION_PLANS
    )

@subscription.route('/checkout/<plan>')
@login_required
@admin_required
def checkout(plan):
    """Redirect to Stripe checkout page for subscription"""
    if plan not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan', 'danger')
        return redirect(url_for('subscription.index'))
    
    organization = Organization.query.get(current_user.organization_id)
    plan_data = SUBSCRIPTION_PLANS[plan]
    
    if plan == 'free':
        # Handle free plan subscription (no payment required)
        handle_free_plan_subscription(organization)
        flash('Your subscription has been updated to the Free plan', 'success')
        return redirect(url_for('subscription.index'))
    
    # Get domain for success and cancel URLs
    domain_url = request.host_url.rstrip('/')
    
    try:
        # Create or update Stripe customer
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
            organization.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan_data['name'],
                        'description': f'Monthly subscription to {plan_data["name"]} for {organization.name}',
                    },
                    'unit_amount': int(plan_data['price'] * 100),  # convert to cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{domain_url}{url_for('subscription.success')}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain_url}{url_for('subscription.cancel')}",
            metadata={
                'organization_id': organization.id,
                'plan': plan
            }
        )
        
        # Redirect to Stripe checkout
        return redirect(checkout_session.url)
    
    except stripe.error.StripeError as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('subscription.index'))

@subscription.route('/success')
@login_required
@admin_required
def success():
    """Handle successful subscription checkout"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid checkout session', 'danger')
        return redirect(url_for('subscription.index'))
    
    try:
        # Retrieve checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Get the subscription ID
            subscription_id = checkout_session.subscription
            
            # Get organization
            organization_id = int(checkout_session.metadata.get('organization_id'))
            organization = Organization.query.get(organization_id)
            
            if organization:
                # Update the organization's subscription
                update_subscription(organization, checkout_session.metadata.get('plan'), subscription_id)
                
                flash('Your subscription has been successfully updated', 'success')
            else:
                flash('Organization not found', 'danger')
        else:
            flash('Payment not completed', 'warning')
    
    except stripe.error.StripeError as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('subscription.index'))

@subscription.route('/cancel')
@login_required
def cancel():
    """Handle cancelled subscription checkout"""
    flash('Subscription checkout was cancelled', 'info')
    return redirect(url_for('subscription.index'))

@subscription.route('/manage')
@login_required
@admin_required
def manage():
    """Redirect to Stripe customer portal"""
    organization = Organization.query.get(current_user.organization_id)
    
    if not organization.stripe_customer_id:
        flash('No subscription information found', 'danger')
        return redirect(url_for('subscription.index'))
    
    try:
        # Create customer portal session
        domain_url = request.host_url.rstrip('/')
        
        portal_session = stripe.billing_portal.Session.create(
            customer=organization.stripe_customer_id,
            return_url=f"{domain_url}{url_for('subscription.index')}"
        )
        
        return redirect(portal_session.url)
    
    except stripe.error.StripeError as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('subscription.index'))

def handle_free_plan_subscription(organization):
    """Handle free plan subscription (no payment required)"""
    # Cancel any existing Stripe subscription
    current_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).first()
    
    if current_subscription and current_subscription.stripe_subscription_id:
        try:
            stripe.Subscription.delete(current_subscription.stripe_subscription_id)
        except stripe.error.StripeError:
            pass
        
        # Mark the current subscription as cancelled
        current_subscription.status = 'cancelled'
        db.session.commit()
    
    # Create new subscription record
    new_subscription = Subscription(
        organization_id=organization.id,
        plan_name='free',
        status='active',
        stripe_subscription_id=None,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),  # Free plan for 1 year
        price=0.00,
        features=json.dumps(SUBSCRIPTION_PLANS['free']['features'])
    )
    
    # Update organization
    organization.subscription_plan = 'free'
    organization.subscription_status = 'active'
    organization.subscription_expires_at = new_subscription.end_date
    
    # Configure features
    organization.enable_badge_printing = False  # Not available in free plan
    
    db.session.add(new_subscription)
    db.session.commit()

def update_subscription(organization, plan, stripe_subscription_id):
    """Update the organization's subscription details"""
    # Cancel existing subscription
    current_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).first()
    
    if current_subscription:
        current_subscription.status = 'cancelled'
        db.session.commit()
    
    # Get plan details
    plan_data = SUBSCRIPTION_PLANS.get(plan)
    if not plan_data:
        return
    
    # Get subscription details from Stripe
    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
    end_timestamp = stripe_sub.current_period_end
    end_date = datetime.fromtimestamp(end_timestamp)
    
    # Create new subscription record
    new_subscription = Subscription(
        organization_id=organization.id,
        plan_name=plan,
        status='active',
        stripe_subscription_id=stripe_subscription_id,
        start_date=datetime.utcnow(),
        end_date=end_date,
        price=plan_data['price'],
        features=json.dumps(plan_data['features'])
    )
    
    # Update organization
    organization.subscription_plan = plan
    organization.subscription_status = 'active'
    organization.subscription_expires_at = end_date
    
    # Configure features based on plan
    features = plan_data['features']
    organization.enable_badge_printing = features.get('badge_printing', False)
    
    db.session.add(new_subscription)
    db.session.commit()