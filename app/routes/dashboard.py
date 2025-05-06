from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Visitor, CheckIn, Staff, Organization

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Get today's date range
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    # Get last 7 days range
    last_week = today - timedelta(days=7)
    
    # Get current organization
    organization = Organization.query.get(current_user.organization_id)
    
    # Get visitor counts
    visitors_count = Visitor.query.filter_by(organization_id=current_user.organization_id).count()
    
    visitors_today = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_in_time >= today,
        CheckIn.check_in_time < tomorrow
    ).count()
    
    visitors_week = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_in_time >= last_week
    ).count()
    
    active_visitors = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.is_active == True
    ).count()
    
    # Get staff count
    staff_count = Staff.query.filter_by(organization_id=current_user.organization_id).count()
    
    # Get recent visitors (for dashboard table)
    recent_visitors = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id
    ).order_by(
        CheckIn.check_in_time.desc()
    ).limit(10).all()
    
    # Get subscription details
    subscription = {
        'plan': organization.subscription_plan,
        'status': organization.subscription_status,
        'expires_at': organization.subscription_expires_at
    }
    
    return render_template('dashboard/index.html',
                          title='Dashboard',
                          visitors_count=visitors_count,
                          visitors_today=visitors_today,
                          visitors_week=visitors_week,
                          active_visitors=active_visitors,
                          staff_count=staff_count,
                          recent_visitors=recent_visitors,
                          subscription=subscription,
                          organization=organization)