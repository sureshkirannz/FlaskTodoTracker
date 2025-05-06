"""
Stripe integration utilities for Visitor Management System.
"""

import os
import stripe
import json
import logging
from datetime import datetime, timedelta
from app.subscription_plans import get_plan

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

logger = logging.getLogger(__name__)

def create_customer(organization, user):
    """
    Create a Stripe customer for an organization.
    
    Args:
        organization: The organization model instance
        user: The admin user for the organization
    
    Returns:
        str: The Stripe customer ID
    """
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=organization.name,
            metadata={
                'organization_id': organization.id,
                'user_id': user.id
            },
            description=f"Organization {organization.name} (ID: {organization.id})"
        )
        return customer.id
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        return None

def update_customer(organization, user=None):
    """
    Update a Stripe customer for an organization.
    
    Args:
        organization: The organization model instance
        user: Optional user to update email
    
    Returns:
        bool: Success status
    """
    if not organization.stripe_customer_id:
        logger.error(f"No Stripe customer ID for organization {organization.id}")
        return False
    
    try:
        update_data = {
            'name': organization.name,
            'metadata': {
                'organization_id': organization.id
            }
        }
        
        if user:
            update_data['email'] = user.email
        
        stripe.Customer.modify(
            organization.stripe_customer_id,
            **update_data
        )
        return True
    except Exception as e:
        logger.error(f"Error updating Stripe customer: {str(e)}")
        return False

def create_subscription(organization, plan_id, billing_cycle='monthly'):
    """
    Create a subscription for an organization.
    
    Args:
        organization: The organization model instance
        plan_id: The subscription plan ID
        billing_cycle: Either 'monthly' or 'yearly'
    
    Returns:
        dict: Subscription details
    """
    if not organization.stripe_customer_id:
        logger.error(f"No Stripe customer ID for organization {organization.id}")
        return None
    
    plan = get_plan(plan_id)
    if not plan:
        logger.error(f"Invalid plan ID: {plan_id}")
        return None
    
    # Get the appropriate Stripe price ID based on billing cycle
    price_id_key = f"stripe_price_id_{billing_cycle}"
    price_id = plan.get(price_id_key)
    
    if not price_id:
        logger.error(f"No Stripe price ID for plan {plan_id} with billing cycle {billing_cycle}")
        return None
    
    try:
        subscription = stripe.Subscription.create(
            customer=organization.stripe_customer_id,
            items=[
                {
                    'price': price_id,
                },
            ],
            metadata={
                'organization_id': organization.id,
                'plan_id': plan_id,
                'billing_cycle': billing_cycle
            }
        )
        
        return {
            'stripe_subscription_id': subscription.id,
            'status': subscription.status,
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'plan_id': plan_id,
            'billing_cycle': billing_cycle
        }
    except Exception as e:
        logger.error(f"Error creating Stripe subscription: {str(e)}")
        return None

def cancel_subscription(stripe_subscription_id):
    """
    Cancel a subscription.
    
    Args:
        stripe_subscription_id: The Stripe subscription ID
    
    Returns:
        bool: Success status
    """
    try:
        stripe.Subscription.delete(stripe_subscription_id)
        return True
    except Exception as e:
        logger.error(f"Error canceling Stripe subscription: {str(e)}")
        return False

def get_subscription(stripe_subscription_id):
    """
    Get subscription details.
    
    Args:
        stripe_subscription_id: The Stripe subscription ID
    
    Returns:
        dict: Subscription details
    """
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'plan_id': subscription.metadata.get('plan_id'),
            'billing_cycle': subscription.metadata.get('billing_cycle')
        }
    except Exception as e:
        logger.error(f"Error retrieving Stripe subscription: {str(e)}")
        return None

def create_checkout_session(organization, plan_id, billing_cycle='monthly', success_url=None, cancel_url=None):
    """
    Create a Stripe Checkout session for subscription signup or change.
    
    Args:
        organization: The organization model instance
        plan_id: The subscription plan ID
        billing_cycle: Either 'monthly' or 'yearly'
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels
    
    Returns:
        str: Checkout session URL
    """
    if not organization.stripe_customer_id:
        logger.error(f"No Stripe customer ID for organization {organization.id}")
        return None
    
    plan = get_plan(plan_id)
    if not plan:
        logger.error(f"Invalid plan ID: {plan_id}")
        return None
    
    # Get the appropriate Stripe price ID based on billing cycle
    price_id_key = f"stripe_price_id_{billing_cycle}"
    price_id = plan.get(price_id_key)
    
    if not price_id:
        logger.error(f"No Stripe price ID for plan {plan_id} with billing cycle {billing_cycle}")
        return None
    
    # Set default URLs if not provided
    if not success_url:
        success_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    
    if not cancel_url:
        cancel_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/subscription/cancel"
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=organization.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'organization_id': organization.id,
                'plan_id': plan_id,
                'billing_cycle': billing_cycle
            }
        )
        
        return checkout_session.url
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {str(e)}")
        return None

def handle_webhook_event(payload, signature, webhook_secret):
    """
    Handle Stripe webhook events.
    
    Args:
        payload: The webhook request body
        signature: The Stripe signature header
        webhook_secret: The webhook secret for validation
    
    Returns:
        dict: The parsed event data
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        
        event_data = {
            'id': event.id,
            'type': event.type,
            'data': event.data.object,
            'created': datetime.fromtimestamp(event.created)
        }
        
        # Handle specific event types
        if event.type == 'customer.subscription.created':
            # New subscription created
            subscription = event.data.object
            event_data['subscription_id'] = subscription.id
            event_data['customer_id'] = subscription.customer
            event_data['status'] = subscription.status
            event_data['organization_id'] = subscription.metadata.get('organization_id')
            event_data['plan_id'] = subscription.metadata.get('plan_id')
        
        elif event.type == 'customer.subscription.updated':
            # Subscription updated (plan change, etc.)
            subscription = event.data.object
            event_data['subscription_id'] = subscription.id
            event_data['customer_id'] = subscription.customer
            event_data['status'] = subscription.status
            event_data['organization_id'] = subscription.metadata.get('organization_id')
            event_data['plan_id'] = subscription.metadata.get('plan_id')
        
        elif event.type == 'customer.subscription.deleted':
            # Subscription canceled or expired
            subscription = event.data.object
            event_data['subscription_id'] = subscription.id
            event_data['customer_id'] = subscription.customer
            event_data['status'] = subscription.status
            event_data['organization_id'] = subscription.metadata.get('organization_id')
        
        elif event.type == 'invoice.payment_succeeded':
            # Invoice payment succeeded
            invoice = event.data.object
            event_data['invoice_id'] = invoice.id
            event_data['customer_id'] = invoice.customer
            event_data['subscription_id'] = invoice.subscription
            event_data['amount_paid'] = invoice.amount_paid / 100  # Convert cents to dollars
        
        elif event.type == 'invoice.payment_failed':
            # Invoice payment failed
            invoice = event.data.object
            event_data['invoice_id'] = invoice.id
            event_data['customer_id'] = invoice.customer
            event_data['subscription_id'] = invoice.subscription
            event_data['amount_due'] = invoice.amount_due / 100  # Convert cents to dollars
        
        return event_data
    
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {str(e)}")
        return None
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {str(e)}")
        return None
    except Exception as e:
        # Other exceptions
        logger.error(f"Error handling webhook: {str(e)}")
        return None