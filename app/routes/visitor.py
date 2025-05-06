from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Visitor, CheckIn, Staff
from app.forms import VisitorCheckInForm, VisitorCheckOutForm, PreregisterVisitorForm, StaffForm
from app.utils import send_checkin_notification, send_checkout_notification, encode_image, generate_badge_data
from datetime import datetime

visitor = Blueprint('visitor', __name__, url_prefix='/visitors')

@visitor.route('/')
@login_required
def index():
    """List all visitors for the organization"""
    visitors = Visitor.query.filter_by(organization_id=current_user.organization_id)\
        .order_by(Visitor.created_at.desc()).all()
    return render_template('visitor/index.html', title='Visitors', visitors=visitors, now=datetime.utcnow)

@visitor.route('/check-in', methods=['GET', 'POST'])
@login_required
def check_in():
    """Check in a visitor"""
    form = VisitorCheckInForm()
    # Populate the staff select field
    form.staff_id.choices = [(s.id, f"{s.first_name} {s.last_name} - {s.department}") 
                            for s in Staff.query.filter_by(organization_id=current_user.organization_id).all()]
    
    if form.validate_on_submit():
        # Check if visitor already exists
        visitor = Visitor.query.filter_by(
            email=form.email.data,
            organization_id=current_user.organization_id
        ).first() if form.email.data else None
        
        # Create new visitor if they don't exist
        if not visitor:
            visitor = Visitor(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                company=form.company.data,
                organization_id=current_user.organization_id,
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
        
        # Send notifications
        send_checkin_notification(checkin)
        
        flash('Visitor checked in successfully', 'success')
        return redirect(url_for('visitor.index'))
    
    return render_template('visitor/check_in.html', title='Check In Visitor', form=form)

@visitor.route('/check-out', methods=['GET', 'POST'])
@login_required
def check_out():
    """Check out a visitor"""
    form = VisitorCheckOutForm()
    
    # Get active check-ins for the organization
    active_checkins = CheckIn.query.join(
        Visitor, CheckIn.visitor_id == Visitor.id
    ).filter(
        Visitor.organization_id == current_user.organization_id,
        CheckIn.check_out_time.is_(None)
    ).all()
    
    # Create visitor choices for the dropdown
    visitor_choices = []
    for checkin in active_checkins:
        visitor = checkin.visitor
        host = checkin.host
        visitor_choices.append((
            checkin.id, 
            f"{visitor.first_name} {visitor.last_name} - {visitor.email}"
        ))
    
    form.visitor_id.choices = visitor_choices
    
    if form.validate_on_submit():
        checkin = CheckIn.query.get(form.visitor_id.data)
        if checkin and checkin.check_out_time is None:
            checkin.check_out_time = datetime.utcnow()
            db.session.commit()
            
            # Send notifications
            send_checkout_notification(checkin)
            
            flash('Visitor checked out successfully', 'success')
            return redirect(url_for('visitor.index'))
        else:
            flash('Invalid check-in record or visitor already checked out', 'danger')
    
    return render_template('visitor/check_out.html', title='Check Out Visitor', form=form)

@visitor.route('/preregister', methods=['GET', 'POST'])
@login_required
def preregister():
    """Preregister a visitor"""
    form = PreregisterVisitorForm()
    # Populate the staff select field
    form.staff_id.choices = [(s.id, f"{s.first_name} {s.last_name} - {s.department}") 
                            for s in Staff.query.filter_by(organization_id=current_user.organization_id).all()]
    
    # Implementation will be added here
    
    return render_template('visitor/preregister.html', title='Preregister Visitor', form=form)

@visitor.route('/view/<int:visitor_id>')
@login_required
def view(visitor_id):
    """View visitor details"""
    visitor = Visitor.query.filter_by(id=visitor_id, organization_id=current_user.organization_id).first_or_404()
    edit_form = StaffForm()  # Using StaffForm as a placeholder for visitor edit form
    
    return render_template('visitor/view.html', title=f'Visitor: {visitor.first_name} {visitor.last_name}', 
                          visitor=visitor, edit_form=edit_form)

@visitor.route('/edit/<int:visitor_id>', methods=['POST'])
@login_required
def edit(visitor_id):
    """Edit visitor information"""
    visitor = Visitor.query.filter_by(id=visitor_id, organization_id=current_user.organization_id).first_or_404()
    
    # Implementation will be added here
    flash('Visitor information updated successfully', 'success')
    return redirect(url_for('visitor.view', visitor_id=visitor.id))