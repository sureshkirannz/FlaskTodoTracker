from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import CheckIn, Visitor, Staff
from app.forms import ReportFilterForm
from app.utils import admin_required

reports = Blueprint('reports', __name__, url_prefix='/reports')

@reports.route('/')
@login_required
def index():
    """Reports dashboard"""
    form = ReportFilterForm()
    
    # Populate the staff select field with organization staff
    staff_list = Staff.query.filter_by(organization_id=current_user.organization_id).all()
    form.staff_id.choices = [(0, 'All Staff')] + [(s.id, f"{s.first_name} {s.last_name}") for s in staff_list]
    
    # Get filter parameters
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    staff_id = request.args.get('staff_id', None)
    purpose = request.args.get('purpose', None)
    
    # Convert dates to datetime if provided
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Set to end of day
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = datetime.utcnow()
    
    # Get checkins based on filters
    query = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_in_time >= start_date,
        CheckIn.check_in_time <= end_date
    )
    
    if staff_id and staff_id != '0':
        query = query.filter(CheckIn.staff_id == int(staff_id))
    
    if purpose:
        query = query.filter(CheckIn.purpose.ilike(f"%{purpose}%"))
    
    checkins = query.order_by(CheckIn.check_in_time.desc()).all()
    
    # Initialize form with current values
    form.start_date.data = start_date.strftime('%Y-%m-%d')
    form.end_date.data = end_date.strftime('%Y-%m-%d')
    if staff_id:
        form.staff_id.data = int(staff_id)
    form.purpose.data = purpose
    
    return render_template(
        'reports/index.html',
        title='Reports',
        form=form,
        checkins=checkins,
        start_date=start_date,
        end_date=end_date
    )

@reports.route('/visitor-stats')
@login_required
def visitor_stats():
    """Get visitor statistics for charts"""
    days = int(request.args.get('days', 30))
    
    # Calculate the date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get daily check-ins count for the period
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        count = CheckIn.query.join(
            Visitor
        ).filter(
            Visitor.organization_id == current_user.organization_id,
            CheckIn.check_in_time >= current_date,
            CheckIn.check_in_time < next_date
        ).count()
        
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count
        })
        
        current_date = next_date
    
    # Get top purpose counts
    purpose_stats = db.session.query(
        CheckIn.purpose, db.func.count(CheckIn.id).label('count')
    ).join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_in_time >= start_date,
        CheckIn.check_in_time <= end_date
    ).group_by(
        CheckIn.purpose
    ).order_by(
        db.func.count(CheckIn.id).desc()
    ).limit(5).all()
    
    purpose_data = [{'purpose': p.purpose or 'Unknown', 'count': p.count} for p in purpose_stats]
    
    # Get top staff visited
    staff_stats = db.session.query(
        Staff.first_name, Staff.last_name, db.func.count(CheckIn.id).label('count')
    ).join(
        CheckIn, Staff.id == CheckIn.staff_id
    ).join(
        Visitor
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_in_time >= start_date,
        CheckIn.check_in_time <= end_date
    ).group_by(
        Staff.id
    ).order_by(
        db.func.count(CheckIn.id).desc()
    ).limit(5).all()
    
    staff_data = [{'name': f"{s.first_name} {s.last_name}", 'count': s.count} for s in staff_stats]
    
    return jsonify({
        'daily': daily_stats,
        'purposes': purpose_data,
        'staff': staff_data
    })