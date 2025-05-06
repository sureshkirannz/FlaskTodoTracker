"""
Subscription plans configuration for Visitor Management System.
This module defines the available subscription plans and their features.
"""

# Define subscription plans and their features
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "description": "Basic visitor management for small organizations",
        "price_monthly": 0,
        "price_yearly": 0,
        "stripe_price_id_monthly": None,  # Free plan doesn't need Stripe price IDs
        "stripe_price_id_yearly": None,
        "features": {
            "visitor_limit": 50,  # Monthly visitor limit
            "staff_limit": 5,     # Staff member limit
            "email_notifications": True,
            "visitor_photo_capture": True,
            "badge_printing": False,
            "document_signing": False,
            "pre_registration": False,
            "reports_export": False,
            "custom_branding": False,
            "api_access": False,
        }
    },
    "basic": {
        "name": "Basic",
        "description": "Professional visitor management for growing organizations",
        "price_monthly": 49,
        "price_yearly": 490,  # Effectively 2 months free
        "stripe_price_id_monthly": "price_basic_monthly",  # Replace with actual Stripe price IDs
        "stripe_price_id_yearly": "price_basic_yearly",
        "features": {
            "visitor_limit": 200,
            "staff_limit": 20,
            "email_notifications": True,
            "visitor_photo_capture": True,
            "badge_printing": True,
            "document_signing": True,
            "pre_registration": True,
            "reports_export": True,
            "custom_branding": False,
            "api_access": False,
        }
    },
    "professional": {
        "name": "Professional",
        "description": "Advanced visitor management for medium businesses",
        "price_monthly": 99,
        "price_yearly": 990,  # Effectively 2 months free
        "stripe_price_id_monthly": "price_professional_monthly",
        "stripe_price_id_yearly": "price_professional_yearly",
        "features": {
            "visitor_limit": 500,
            "staff_limit": 50,
            "email_notifications": True,
            "visitor_photo_capture": True,
            "badge_printing": True,
            "document_signing": True,
            "pre_registration": True,
            "reports_export": True,
            "custom_branding": True,
            "api_access": False,
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "Complete visitor management for large organizations",
        "price_monthly": 199,
        "price_yearly": 1990,  # Effectively 2 months free
        "stripe_price_id_monthly": "price_enterprise_monthly",
        "stripe_price_id_yearly": "price_enterprise_yearly",
        "features": {
            "visitor_limit": 2000,
            "staff_limit": 200,
            "email_notifications": True,
            "visitor_photo_capture": True,
            "badge_printing": True,
            "document_signing": True,
            "pre_registration": True,
            "reports_export": True,
            "custom_branding": True,
            "api_access": True,
        }
    },
}

def get_plan(plan_id):
    """Get a subscription plan by its ID."""
    return SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])

def get_all_plans():
    """Get all available subscription plans."""
    return SUBSCRIPTION_PLANS

def get_plan_feature(plan_id, feature_name):
    """Get a specific feature value for a plan."""
    plan = get_plan(plan_id)
    return plan["features"].get(feature_name)

def compare_plans():
    """Generate a comparison of all subscription plans."""
    plans = get_all_plans()
    plan_ids = list(plans.keys())
    feature_sets = {}
    
    # Collect all unique features
    for plan_id, plan in plans.items():
        for feature, value in plan["features"].items():
            if feature not in feature_sets:
                feature_sets[feature] = {}
            feature_sets[feature][plan_id] = value
    
    return {
        "plan_ids": plan_ids,
        "plans": plans,
        "feature_sets": feature_sets
    }

def is_feature_available(organization, feature_name):
    """Check if a feature is available for an organization's subscription plan."""
    plan_id = organization.subscription_plan
    return get_plan_feature(plan_id, feature_name)

def check_limit(organization, limit_name, current_count):
    """Check if a limit has been reached for an organization's subscription plan."""
    plan_id = organization.subscription_plan
    limit = get_plan_feature(plan_id, limit_name)
    
    # If limit is None or 0, assume unlimited
    if not limit:
        return True
        
    return current_count < limit