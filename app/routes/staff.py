from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Staff
from app.forms import StaffForm
from app.utils import encode_image

staff = Blueprint('staff', __name__, url_prefix='/staff')

@staff.route('/')
@login_required
def index():
    """List all staff members for the organization"""
    staff_members = Staff.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('staff/index.html', title='Staff', staff_members=staff_members)

@staff.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new staff member"""
    form = StaffForm()
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Staff member added successfully', 'success')
        return redirect(url_for('staff.index'))
    
    return render_template('staff/add.html', title='Add Staff Member', form=form)

@staff.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a staff member"""
    staff_member = Staff.query.filter_by(
        id=id, organization_id=current_user.organization_id
    ).first_or_404()
    
    form = StaffForm(obj=staff_member)
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Staff member updated successfully', 'success')
        return redirect(url_for('staff.index'))
    
    return render_template('staff/edit.html', title='Edit Staff Member', form=form, staff_member=staff_member)

@staff.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a staff member"""
    staff_member = Staff.query.filter_by(
        id=id, organization_id=current_user.organization_id
    ).first_or_404()
    
    # Implementation will be added here
    flash('Staff member deleted successfully', 'success')
    return redirect(url_for('staff.index'))