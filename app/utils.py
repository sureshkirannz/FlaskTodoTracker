import os
import json
import base64
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, url_for, current_app, render_template
from flask_login import current_user
from flask_mail import Message
import stripe
from app import db, mail
from app.models import CheckIn, EmailTemplate, Organization

# Set up Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Configure logger
logger = logging.getLogger(__name__)

def admin_required(f):
    """
    Decorator for views that require admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def encode_image(image_data):
    """
    Encode image data to base64 for storing in database
    """
    if not image_data:
        return None
    
    try:
        encoded = base64.b64encode(image_data).decode('utf-8')
        return encoded
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        return None

def decode_image(base64_string):
    """
    Decode base64 string to image data
    """
    if not base64_string:
        return None
    
    try:
        decoded = base64.b64decode(base64_string)
        return decoded
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        return None

def auto_checkout_visitors():
    """
    Auto-checkout visitors after 24 hours if enabled
    Run as a scheduled task
    """
    try:
        # Get organizations with auto-checkout enabled
        orgs = Organization.query.filter_by(enable_auto_checkout=True).all()
        
        for org in orgs:
            # Find active check-ins older than 24 hours
            checkout_time = datetime.utcnow()
            checkin_cutoff = checkout_time - timedelta(hours=24)
            
            active_checkins = CheckIn.query.filter_by(
                is_active=True
            ).join(
                'visitor'
            ).filter(
                CheckIn.check_in_time < checkin_cutoff,
                CheckIn.visitor.has(organization_id=org.id)
            ).all()
            
            for checkin in active_checkins:
                # Perform checkout
                checkin.is_active = False
                checkin.check_out_time = checkout_time
                db.session.add(checkin)
                
                # Send notification if enabled
                if org.enable_email_notifications:
                    send_checkout_notification(checkin)
            
            if active_checkins:
                db.session.commit()
                logger.info(f"Auto-checked out {len(active_checkins)} visitors for organization {org.id}")
    
    except Exception as e:
        logger.error(f"Error in auto-checkout: {e}")

def send_password_reset_email(user):
    """
    Send password reset email to user
    """
    token = user.get_reset_password_token()
    msg = Message(
        subject='Password Reset Request',
        recipients=[user.email],
        html=render_template('email/reset_password.html', user=user, token=token),
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")

def send_checkin_notification(checkin):
    """
    Send email notification for visitor check-in
    """
    try:
        # Get visitor and host data
        visitor = checkin.visitor
        host = checkin.host
        organization = Organization.query.get(visitor.organization_id)
        
        # Get email template
        template = EmailTemplate.query.filter_by(
            organization_id=visitor.organization_id,
            template_type='check_in'
        ).first()
        
        if not template or not host or not host.email:
            return
        
        # Send email
        msg = Message(
            subject=template.subject,
            recipients=[host.email],
            html=render_template('email/visitor_checkin.html', 
                visitor=visitor, 
                checkin=checkin,
                host=host,
                organization=organization
            ),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        logger.info(f"Sent check-in notification for visitor {visitor.id} to host {host.id}")
    
    except Exception as e:
        logger.error(f"Error sending check-in notification: {e}")

def send_checkout_notification(checkin):
    """
    Send email notification for visitor check-out
    """
    try:
        # Get visitor and host data
        visitor = checkin.visitor
        host = checkin.host
        organization = Organization.query.get(visitor.organization_id)
        
        # Get email template
        template = EmailTemplate.query.filter_by(
            organization_id=visitor.organization_id,
            template_type='check_out'
        ).first()
        
        if not template or not host or not host.email:
            return
        
        # Send email
        msg = Message(
            subject=template.subject,
            recipients=[host.email],
            html=render_template('email/visitor_checkout.html', 
                visitor=visitor, 
                checkin=checkin,
                host=host,
                organization=organization
            ),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        logger.info(f"Sent check-out notification for visitor {visitor.id} to host {host.id}")
    
    except Exception as e:
        logger.error(f"Error sending check-out notification: {e}")

def print_badge(badge_id):
    """
    Print a visitor badge using CUPS
    """
    # This is a placeholder for badge printing functionality
    # In production, this would interact with a printer API or CUPS
    logger.info(f"Print request for badge {badge_id}")
    return True

def generate_badge_data(checkin_id):
    """
    Generate badge data for a check-in
    """
    try:
        checkin = CheckIn.query.get(checkin_id)
        if not checkin:
            return None
        
        visitor = checkin.visitor
        host = checkin.host
        organization = Organization.query.get(visitor.organization_id)
        
        # Create badge data dictionary
        badge_data = {
            'visitor_name': f"{visitor.first_name} {visitor.last_name}",
            'company': visitor.company or 'Guest',
            'check_in_time': checkin.check_in_time.strftime('%Y-%m-%d %H:%M'),
            'host_name': f"{host.first_name} {host.last_name}" if host else 'N/A',
            'organization_name': organization.name,
            'photo': visitor.photo if visitor.photo else None,
            'badge_type': 'visitor'
        }
        
        return json.dumps(badge_data)
    
    except Exception as e:
        logger.error(f"Error generating badge data: {e}")
        return None

def create_default_email_templates(organization_id):
    """
    Create default email templates for a new organization
    """
    templates = [
        {
            'name': 'Visitor Check-in Notification',
            'subject': 'Visitor Check-in Notification',
            'body': render_template('email/default_checkin_template.html'),
            'template_type': 'check_in'
        },
        {
            'name': 'Visitor Check-out Notification',
            'subject': 'Visitor Check-out Notification',
            'body': render_template('email/default_checkout_template.html'),
            'template_type': 'check_out'
        },
        {
            'name': 'Visitor Preregistration Confirmation',
            'subject': 'Your Visit Has Been Registered',
            'body': render_template('email/default_preregister_template.html'),
            'template_type': 'preregister'
        }
    ]
    
    for template_data in templates:
        template = EmailTemplate(
            name=template_data['name'],
            subject=template_data['subject'],
            body=template_data['body'],
            template_type=template_data['template_type'],
            organization_id=organization_id
        )
        db.session.add(template)
    
    try:
        db.session.commit()
        logger.info(f"Created default email templates for organization {organization_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default email templates: {e}")

def create_default_badge_template(organization_id):
    """
    Create a default badge template for a new organization
    """
    try:
        # Default badge template (JSON format)
        default_template = {
            'width': '3.5in',
            'height': '2in',
            'elements': [
                {
                    'type': 'text',
                    'content': '{{visitor_name}}',
                    'x': '50%',
                    'y': '40%',
                    'align': 'center',
                    'font_size': '16pt',
                    'font_weight': 'bold'
                },
                {
                    'type': 'text',
                    'content': '{{company}}',
                    'x': '50%',
                    'y': '50%',
                    'align': 'center',
                    'font_size': '12pt'
                },
                {
                    'type': 'text',
                    'content': 'Host: {{host_name}}',
                    'x': '50%',
                    'y': '65%',
                    'align': 'center',
                    'font_size': '10pt'
                },
                {
                    'type': 'text',
                    'content': '{{check_in_time}}',
                    'x': '50%',
                    'y': '75%',
                    'align': 'center',
                    'font_size': '8pt'
                },
                {
                    'type': 'text',
                    'content': 'VISITOR',
                    'x': '50%',
                    'y': '90%',
                    'align': 'center',
                    'font_size': '14pt',
                    'font_weight': 'bold',
                    'color': '#ff0000'
                },
                {
                    'type': 'image',
                    'content': '{{photo}}',
                    'x': '50%',
                    'y': '20%',
                    'width': '1in',
                    'height': '1in',
                    'align': 'center'
                },
                {
                    'type': 'text',
                    'content': '{{organization_name}}',
                    'x': '50%',
                    'y': '5%',
                    'align': 'center',
                    'font_size': '12pt',
                    'font_weight': 'bold'
                }
            ]
        }
        
        organization = Organization.query.get(organization_id)
        if organization:
            organization.badge_template = json.dumps(default_template)
            db.session.commit()
            logger.info(f"Created default badge template for organization {organization_id}")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default badge template: {e}")

def init_scheduler(app):
    """
    Initialize scheduler for background tasks
    """
    try:
        from flask_apscheduler import APScheduler
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        
        # Add auto-checkout job to run every hour
        scheduler.add_job(
            id='auto_checkout_visitors',
            func=auto_checkout_visitors,
            trigger='interval',
            hours=1
        )
        
        logger.info("Scheduler initialized and auto-checkout job added")
    
    except Exception as e:
        logger.error(f"Error initializing scheduler: {e}")