from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import current_user
from datetime import datetime

from app import db
from app.models import Organization, Staff, Visitor, CheckIn
from app.forms import VisitorCheckInForm, VisitorCheckOutForm
from app.utils import send_checkin_notification, send_checkout_notification, generate_badge_data, log_action

kiosk = Blueprint('kiosk', __name__)

@kiosk.route('/')
def index():
    """Kiosk selection screen"""
    # Get all active organizations
    organizations = Organization.query.filter_by(is_active=True).all()
    
    return render_template('kiosk/index.html', 
                          organizations=organizations,
                          title="Visitor Kiosk")

@kiosk.route('/org/<int:org_id>')
def organization(org_id):
    """Organization-specific kiosk landing page"""
    organization = Organization.query.get_or_404(org_id)
    
    # Verify organization is active
    if not organization.is_active:
        flash('This organization is not active.', 'danger')
        return redirect(url_for('kiosk.index'))
    
    return render_template('kiosk/organization.html',
                          organization=organization,
                          title=f"Visitor Kiosk - {organization.name}")

@kiosk.route('/org/<int:org_id>/check-in', methods=['GET', 'POST'])
def check_in(org_id):
    """Visitor check-in form"""
    organization = Organization.query.get_or_404(org_id)
    
    # Verify organization is active
    if not organization.is_active:
        flash('This organization is not active.', 'danger')
        return redirect(url_for('kiosk.index'))
    
    # Get staff for selection dropdown
    staff_choices = [(s.id, f"{s.first_name} {s.last_name} - {s.department}") for s in 
                     Staff.query.filter_by(organization_id=org_id, is_active=True).all()]
    
    # Create form with staff choices
    form = VisitorCheckInForm()
    form.staff_id.choices = staff_choices
    
    if form.validate_on_submit():
        # Check if visitor already exists
        visitor = Visitor.query.filter_by(
            email=form.email.data, 
            organization_id=org_id
        ).first() if form.email.data else None
        
        # Create new visitor if they don't exist
        if not visitor:
            visitor = Visitor(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                company=form.company.data,
                organization_id=org_id,
                created_at=datetime.utcnow()
            )
            db.session.add(visitor)
            db.session.flush()  # Get ID without committing
        
        # Create check-in record
        checkin = CheckIn(
            visitor_id=visitor.id,
            staff_id=form.staff_id.data,
            purpose=form.purpose.data,
            check_in_time=datetime.utcnow()
        )
        db.session.add(checkin)
        db.session.commit()
        
        # Log the action
        log_action('visitor_check_in', {
            'visitor_id': visitor.id,
            'visitor_name': f"{visitor.first_name} {visitor.last_name}",
            'staff_id': form.staff_id.data,
            'check_in_time': checkin.check_in_time.isoformat()
        })
        
        # Send notifications
        send_checkin_notification(checkin)
        
        # Generate badge if enabled
        if organization.enable_badge_printing:
            badge_data = generate_badge_data(checkin)
        
        flash(f'Welcome, {visitor.first_name}! You have been checked in successfully.', 'success')
        return redirect(url_for('kiosk.success', org_id=org_id))
    
    return render_template('kiosk/check_in.html',
                          organization=organization,
                          form=form,
                          title=f"Visitor Check-In - {organization.name}")

@kiosk.route('/org/<int:org_id>/check-out', methods=['GET', 'POST'])
def check_out(org_id):
    """Visitor check-out form"""
    organization = Organization.query.get_or_404(org_id)
    
    # Get search parameter
    email = request.args.get('email', '')
    
    # Get active check-ins, filtered by email if provided
    query = CheckIn.query.join(
        Visitor, CheckIn.visitor_id == Visitor.id
    ).filter(
        Visitor.organization_id == org_id,
        CheckIn.check_out_time.is_(None)
    )
    
    if email:
        query = query.filter(Visitor.email.ilike(f'%{email}%'))
    
    active_checkins = query.all()
    
    # Verify organization is active
    if not organization.is_active:
        flash('This organization is not active.', 'danger')
        return redirect(url_for('kiosk.index'))
    
    # Get active check-ins for the organization
    active_checkins = CheckIn.query.join(
        Visitor, CheckIn.visitor_id == Visitor.id
    ).filter(
        Visitor.organization_id == org_id,
        CheckIn.check_out_time.is_(None)
    ).all()
    
    # Create visitor choices for the dropdown
    visitor_choices = []
    for checkin in active_checkins:
        visitor = checkin.visitor
        host = checkin.host
        visitor_choices.append((
            checkin.id, 
            f"{visitor.first_name} {visitor.last_name} - Visiting {host.first_name if host else 'N/A'}"
        ))
    
    # Create form with visitor choices
    form = VisitorCheckOutForm()
    form.visitor_id.choices = visitor_choices
    
    if form.validate_on_submit():
        checkin_id = form.visitor_id.data
        checkin = CheckIn.query.get(checkin_id)
        
        if checkin and checkin.check_out_time is None:
            # Update check-out time
            checkin.check_out_time = datetime.utcnow()
            db.session.commit()
            
            # Log the action
            visitor = checkin.visitor
            log_action('visitor_check_out', {
                'visitor_id': visitor.id,
                'visitor_name': f"{visitor.first_name} {visitor.last_name}",
                'staff_id': checkin.staff_id,
                'check_in_time': checkin.check_in_time.isoformat(),
                'check_out_time': checkin.check_out_time.isoformat()
            })
            
            # Send notifications
            send_checkout_notification(checkin)
            
            flash(f'Thank you, {visitor.first_name}! You have been checked out successfully.', 'success')
            return redirect(url_for('kiosk.success', org_id=org_id))
        else:
            flash('Invalid check-in record or visitor already checked out.', 'danger')
    
    return render_template('kiosk/check_out.html',
                          organization=organization,
                          form=form,
                          title=f"Visitor Check-Out - {organization.name}")

@kiosk.route('/org/<int:org_id>/success')
def success(org_id):
    """Success page after check-in/check-out"""
    organization = Organization.query.get_or_404(org_id)
    
    # Verify organization is active
    if not organization.is_active:
        flash('This organization is not active.', 'danger')
        return redirect(url_for('kiosk.index'))
    
    return render_template('kiosk/success.html',
                          organization=organization,
                          title=f"Success - {organization.name}")

@kiosk.route('/org/<int:org_id>/exit-kiosk', methods=['POST'])
def exit_kiosk(org_id):
    """Exit kiosk mode with passcode"""
    organization = Organization.query.get_or_404(org_id)
    
    # Get passcode from request
    passcode = request.form.get('passcode')
    
    # Check passcode against organization settings or use default
    if passcode == organization.kiosk_passcode or passcode == current_app.config['DEFAULT_KIOSK_PASSCODE']:
        # Log the action
        log_action('kiosk_exit', {
            'organization_id': org_id,
            'organization_name': organization.name
        })
        
        flash('Successfully exited kiosk mode.', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Invalid passcode. Please try again.', 'danger')
        return redirect(url_for('kiosk.organization', org_id=org_id))