from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from app import db
from app.models import Organization, Staff, Visitor, CheckIn, Badge
from app.forms import VisitorCheckInForm, VisitorCheckOutForm
from app.utils import send_checkin_notification, send_checkout_notification, encode_image, generate_badge_data
from datetime import datetime

kiosk = Blueprint('kiosk', __name__, url_prefix='/kiosk')

@kiosk.route('/')
def index():
    """Kiosk mode landing page - organization selection"""
    # Get all organizations
    organizations = Organization.query.all()
    return render_template('kiosk/select_organization.html', 
                          title='Visitor Kiosk', 
                          organizations=organizations)

@kiosk.route('/<int:org_id>')
def organization(org_id):
    """Kiosk mode for specific organization"""
    organization = Organization.query.get_or_404(org_id)
    return render_template('kiosk/organization.html', title='Visitor Check-In', organization=organization)

@kiosk.route('/<int:org_id>/check-in', methods=['GET', 'POST'])
def check_in(org_id):
    """Visitor check-in form"""
    organization = Organization.query.get_or_404(org_id)
    form = VisitorCheckInForm()
    
    # Populate the staff select field
    staff_list = Staff.query.filter_by(organization_id=org_id).all()
    form.staff_id.choices = [(s.id, f"{s.first_name} {s.last_name} - {s.department}") for s in staff_list]
    
    if form.validate_on_submit():
        # Implementation will be added here
        flash('You have been checked in successfully', 'success')
        return redirect(url_for('kiosk.success', org_id=org_id))
    
    return render_template('kiosk/check_in.html', 
                         title='Visitor Check-In', 
                         form=form, 
                         organization=organization,
                         enable_photo=organization.enable_photo_capture)

@kiosk.route('/<int:org_id>/check-out', methods=['GET', 'POST'])
def check_out(org_id):
    """Visitor check-out form"""
    organization = Organization.query.get_or_404(org_id)
    form = VisitorCheckOutForm()
    
    # Get all active check-ins for the organization
    active_checkins = CheckIn.query.join(
        Visitor
    ).filter(
        Visitor.organization_id == org_id,
        CheckIn.is_active == True
    ).all()
    
    # Create list of active visitors
    visitors = []
    for checkin in active_checkins:
        visitors.append((checkin.visitor_id, f"{checkin.visitor.first_name} {checkin.visitor.last_name}"))
    
    form.visitor_id.choices = visitors
    
    if form.validate_on_submit():
        # Implementation will be added here
        flash('You have been checked out successfully', 'success')
        return redirect(url_for('kiosk.success', org_id=org_id))
    
    return render_template('kiosk/check_out.html', title='Visitor Check-Out', form=form, organization=organization)

@kiosk.route('/<int:org_id>/success')
def success(org_id):
    """Success page after check-in/out"""
    organization = Organization.query.get_or_404(org_id)
    return render_template('kiosk/success.html', title='Success', organization=organization)

@kiosk.route('/<int:org_id>/staff/<int:staff_id>')
def staff_info(org_id, staff_id):
    """Get staff information for display in kiosk"""
    organization = Organization.query.get_or_404(org_id)
    staff = Staff.query.filter_by(id=staff_id, organization_id=org_id).first_or_404()
    
    return jsonify({
        'id': staff.id,
        'first_name': staff.first_name,
        'last_name': staff.last_name,
        'department': staff.department,
        'position': staff.position,
        'photo': staff.photo
    })