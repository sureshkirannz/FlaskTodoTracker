from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app import db
from app.models import Visitor, CheckIn, Staff
from app.forms import ReportFilterForm
from collections import defaultdict
from datetime import datetime, timedelta

reports = Blueprint('reports', __name__, url_prefix='/reports')

@reports.route('/')
@login_required
def index():
    """Generate reports based on filters"""
    form = ReportFilterForm()
    # Populate staff dropdown
    form.staff_id.choices = [(0, 'All Staff')] + [
        (s.id, f"{s.first_name} {s.last_name}") 
        for s in Staff.query.filter_by(organization_id=current_user.organization_id).all()
    ]
    
    # Get query parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    staff_id = request.args.get('staff_id', '0')
    purpose = request.args.get('purpose', '')
    
    # Set initial query
    query = CheckIn.query.join(Visitor).filter(
        Visitor.organization_id == current_user.organization_id
    )
    
    # Apply filters if provided
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(CheckIn.check_in_time >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(CheckIn.check_in_time <= end_date_obj)
        except ValueError:
            pass
    
    if staff_id and staff_id != '0':
        query = query.filter(CheckIn.staff_id == int(staff_id))
    
    if purpose:
        query = query.filter(CheckIn.purpose.ilike(f'%{purpose}%'))
    
    # Execute query
    checkins = query.order_by(CheckIn.check_in_time.desc()).all()
    
    # Calculate statistics
    total_checkins = len(checkins)
    unique_visitors = len(set(c.visitor_id for c in checkins))
    
    # Calculate average duration (only for checked out visits)
    completed_visits = [c for c in checkins if c.check_out_time]
    if completed_visits:
        total_duration = sum((c.check_out_time - c.check_in_time).total_seconds() for c in completed_visits)
        avg_duration = total_duration / len(completed_visits) / 60  # In minutes
    else:
        avg_duration = 0
    
    # Find most visited host
    host_visits = defaultdict(int)
    for checkin in checkins:
        if checkin.host:
            host_name = f"{checkin.host.first_name} {checkin.host.last_name}"
            host_visits[host_name] += 1
    
    most_visited_host = max(host_visits.items(), key=lambda x: x[1])[0] if host_visits else "N/A"
    
    # Calculate first-time vs returning visitors
    visitor_counts = defaultdict(int)
    for checkin in checkins:
        visitor_counts[checkin.visitor_id] += 1
    
    first_time_visitors = sum(1 for count in visitor_counts.values() if count == 1)
    returning_visitors = unique_visitors - first_time_visitors
    
    # Calculate visit frequency by date
    visit_frequency = defaultdict(int)
    for checkin in checkins:
        date_str = checkin.check_in_time.strftime('%Y-%m-%d')
        visit_frequency[date_str] += 1
    
    # Sort by date
    visit_frequency = dict(sorted(visit_frequency.items()))
    
    return render_template('reports/index.html', title='Reports',
                          form=form,
                          checkins=checkins,
                          total_checkins=total_checkins,
                          unique_visitors=unique_visitors,
                          avg_duration=avg_duration,
                          most_visited_host=most_visited_host,
                          first_time_visitors=first_time_visitors,
                          returning_visitors=returning_visitors,
                          visit_frequency=visit_frequency)

@reports.route('/visitor/<int:visitor_id>')
@login_required
def visitor(visitor_id):
    """Generate report for a specific visitor"""
    visitor = Visitor.query.filter_by(id=visitor_id, organization_id=current_user.organization_id).first_or_404()
    
    # For now, just redirect to visitor view page
    return render_template('visitor/view.html', title=f'Visitor Report: {visitor.first_name} {visitor.last_name}',
                          visitor=visitor, edit_form=None)