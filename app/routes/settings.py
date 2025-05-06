from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Organization, EmailTemplate, Document
from app.forms import OrganizationSettingsForm, EmailTemplateForm, DocumentForm, BadgeTemplateForm
from app.utils import encode_image, admin_required

settings = Blueprint('settings', __name__, url_prefix='/settings')

@settings.route('/')
@login_required
def index():
    """Organization settings dashboard"""
    organization = Organization.query.get(current_user.organization_id)
    return render_template('settings/index.html', title='Settings', organization=organization)

@settings.route('/organization', methods=['GET', 'POST'])
@login_required
@admin_required
def organization():
    """Edit organization settings"""
    organization = Organization.query.get(current_user.organization_id)
    form = OrganizationSettingsForm(obj=organization)
    
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Organization settings saved successfully', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/organization.html', title='Organization Settings', form=form, organization=organization)

@settings.route('/email-templates')
@login_required
@admin_required
def email_templates():
    """List all email templates"""
    templates = EmailTemplate.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('settings/email_templates.html', title='Email Templates', templates=templates)

@settings.route('/email-templates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_email_template(id):
    """Edit an email template"""
    template = EmailTemplate.query.filter_by(
        id=id, organization_id=current_user.organization_id
    ).first_or_404()
    
    form = EmailTemplateForm(obj=template)
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Email template updated successfully', 'success')
        return redirect(url_for('settings.email_templates'))
    
    return render_template('settings/edit_email_template.html', title='Edit Email Template', form=form, template=template)

@settings.route('/documents')
@login_required
@admin_required
def documents():
    """List all documents"""
    documents = Document.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('settings/documents.html', title='Documents', documents=documents)

@settings.route('/documents/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_document():
    """Add a new document"""
    form = DocumentForm()
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Document added successfully', 'success')
        return redirect(url_for('settings.documents'))
    
    return render_template('settings/add_document.html', title='Add Document', form=form)

@settings.route('/badge-template', methods=['GET', 'POST'])
@login_required
@admin_required
def badge_template():
    """Edit badge template"""
    organization = Organization.query.get(current_user.organization_id)
    form = BadgeTemplateForm()
    
    if organization.badge_template:
        # Pre-populate form with existing badge template
        if not form.template_data.data:
            form.template_data.data = organization.badge_template
    
    if form.validate_on_submit():
        # Implementation will be added here
        flash('Badge template saved successfully', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/badge_template.html', title='Badge Template', form=form, organization=organization)

@settings.route('/kiosk-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def kiosk_settings():
    """Edit kiosk settings"""
    organization = Organization.query.get(current_user.organization_id)
    
    if request.method == 'POST':
        # Update kiosk settings
        organization.enable_photo_capture = 'enable_photo_capture' in request.form
        organization.enable_badge_printing = 'enable_badge_printing' in request.form
        organization.enable_auto_checkout = 'enable_auto_checkout' in request.form
        organization.auto_checkout_delay = request.form.get('auto_checkout_delay', 8)
        
        db.session.commit()
        flash('Kiosk settings updated successfully', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/kiosk_settings.html', title='Kiosk Settings', organization=organization)