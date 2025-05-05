import os
import json
import base64
import io
from functools import wraps
from datetime import datetime, timedelta
from flask import url_for, current_app, render_template, abort
from flask_login import current_user
from flask_mail import Message
import stripe
from app import mail, db
from app.models import Organization, EmailTemplate, Document, Badge, Log

# Set Stripe API key
if os.environ.get('STRIPE_SECRET_KEY'):
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def send_email(subject, recipients, text_body, html_body, sender=None, cc=None, bcc=None, attachments=None):
    """
    Send an email with optional cc, bcc, and attachments
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipients
        text_body (str): Plain text email body
        html_body (str): HTML email body
        sender (str, optional): Email sender. Defaults to config MAIL_DEFAULT_SENDER.
        cc (list, optional): List of cc recipients
        bcc (list, optional): List of bcc recipients
        attachments (list, optional): List of attachment dicts with keys 'filename', 'content_type', and 'data'
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not sender:
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Add CC recipients if provided
    if cc:
        msg.cc = cc
        
    # Add BCC recipients if provided
    if bcc:
        msg.bcc = bcc
        
    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            msg.attach(
                filename=attachment['filename'],
                content_type=attachment['content_type'],
                data=attachment['data']
            )
    
    # Log the email
    log_action('email_sent', {
        'to': recipients,
        'subject': subject,
        'cc': cc,
        'bcc': bcc,
        'has_attachments': bool(attachments)
    })
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_welcome_email(user, organization):
    """Send welcome email to newly registered user"""
    login_url = url_for('auth.login', _external=True)
    current_year = datetime.utcnow().year
    
    send_email(
        subject=f'Welcome to {organization.name} Visitor Management System',
        recipients=[user.email],
        text_body=render_template('email/welcome.txt',
                                  user=user,
                                  organization=organization,
                                  url=login_url,
                                  current_year=current_year),
        html_body=render_template('email/welcome.html',
                                  user=user,
                                  organization=organization,
                                  url=login_url,
                                  current_year=current_year)
    )

def send_password_reset_email(user):
    """Send password reset email"""
    token = user.get_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    send_email(
        subject='Reset Your Password',
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', 
                                  user=user, 
                                  reset_url=reset_url),
        html_body=render_template('email/reset_password.html', 
                                  user=user, 
                                  reset_url=reset_url)
    )

def send_checkin_notification(checkin):
    """Send email notification for visitor check-in"""
    send_visitor_notification(checkin, is_checkout=False)

def send_visitor_notification(checkin, is_checkout=False):
    """
    Send email notification for visitor check-in or check-out
    
    Args:
        checkin: The CheckIn model instance
        is_checkout: Boolean indicating if this is a checkout notification (default: False)
    """
    organization = Organization.query.get(checkin.visitor.organization_id)
    if not organization.enable_email_notifications:
        return
    
    # Get host staff member
    host = checkin.host
    if not host or not host.email:
        return
    
    # Calculate duration for checkout
    duration = ''
    if is_checkout and checkin.check_out_time and checkin.check_in_time:
        delta = checkin.check_out_time - checkin.check_in_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        duration = f"{hours} hours, {minutes} minutes"
    
    # Get template from database or use default
    template_type = 'check_out' if is_checkout else 'check_in'
    template = EmailTemplate.query.filter_by(
        organization_id=organization.id,
        template_type=template_type
    ).first()
    
    if template:
        # Use custom template from database
        # Format datetime
        check_in_time = checkin.check_in_time.strftime('%Y-%m-%d %H:%M')
        check_out_time = checkin.check_out_time.strftime('%Y-%m-%d %H:%M') if checkin.check_out_time else 'Not checked out'
        
        # Prepare context for template rendering
        context = {
            'visitor_name': f"{checkin.visitor.first_name} {checkin.visitor.last_name}",
            'visitor_email': checkin.visitor.email or '',
            'visitor_company': checkin.visitor.company or '',
            'visitor_purpose': checkin.purpose,
            'check_in_time': check_in_time,
            'check_out_time': check_out_time,
            'duration': duration,
            'host_name': f"{host.first_name} {host.last_name}",
            'organization_name': organization.name
        }
        
        # Replace placeholders in template
        subject = template.subject
        body = template.body
        
        for key, value in context.items():
            placeholder = '{{' + key + '}}'
            if value:
                subject = subject.replace(placeholder, value)
                body = body.replace(placeholder, value)
            else:
                subject = subject.replace(placeholder, '')
                body = body.replace(placeholder, '')
                
        send_email(
            subject=subject,
            recipients=[host.email],
            text_body=body,
            html_body=body
        )
    else:
        # Use built-in template
        current_year = datetime.utcnow().year
        
        if is_checkout:
            subject = f"Visitor Check-out: {checkin.visitor.first_name} {checkin.visitor.last_name} has departed"
        else:
            subject = f"Visitor Check-in: {checkin.visitor.first_name} {checkin.visitor.last_name} has arrived"
            
        send_email(
            subject=subject,
            recipients=[host.email],
            text_body=render_template('email/visit_notification.txt',
                                     visitor=checkin.visitor,
                                     checkin=checkin,
                                     host=host,
                                     organization=organization,
                                     is_checkout=is_checkout,
                                     duration=duration,
                                     current_year=current_year),
            html_body=render_template('email/visit_notification.html',
                                     visitor=checkin.visitor,
                                     checkin=checkin,
                                     host=host,
                                     organization=organization,
                                     is_checkout=is_checkout,
                                     duration=duration,
                                     current_year=current_year)
        )

def send_checkout_notification(checkin):
    """Send email notification for visitor check-out"""
    send_visitor_notification(checkin, is_checkout=True)

def encode_image(image_file):
    """Encode an image file to base64"""
    if not image_file:
        return None
    
    try:
        # Save the file to a BytesIO object
        img_data = image_file.read()
        
        # Encode to base64
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        return img_b64
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

def generate_badge_data(checkin):
    """Generate badge data for printing"""
    organization = Organization.query.get(checkin.visitor.organization_id)
    
    # Check if badge printing is enabled
    if not organization.enable_badge_printing:
        return None
    
    # Get badge template
    badge_template = organization.badge_template
    if not badge_template:
        # Use default template if none is defined
        badge_template = json.dumps({
            'layout': 'portrait',
            'width': '3.5in',
            'height': '2in',
            'elements': [
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '15%',
                    'align': 'center',
                    'text': organization.name,
                    'fontSize': '16pt',
                    'fontWeight': 'bold'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '25%',
                    'align': 'center',
                    'text': 'VISITOR',
                    'fontSize': '14pt'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '40%',
                    'align': 'center',
                    'text': '{{visitor_name}}',
                    'fontSize': '18pt',
                    'fontWeight': 'bold'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '50%',
                    'align': 'center',
                    'text': '{{visitor_company}}',
                    'fontSize': '12pt'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '60%',
                    'align': 'center',
                    'text': 'Visiting: {{host_name}}',
                    'fontSize': '12pt'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '70%',
                    'align': 'center',
                    'text': '{{check_in_date}}',
                    'fontSize': '12pt'
                },
                {
                    'type': 'text',
                    'x': '50%',
                    'y': '85%',
                    'align': 'center',
                    'text': 'Please return badge upon departure',
                    'fontSize': '10pt'
                }
            ]
        })
    
    # Parse template
    try:
        template = json.loads(badge_template)
    except:
        # Return default template if parsing fails
        template = {
            'layout': 'portrait',
            'width': '3.5in',
            'height': '2in',
            'elements': []
        }
    
    # Get visitor and host information
    visitor = checkin.visitor
    host = checkin.host
    
    # Prepare context for template
    context = {
        'visitor_name': f"{visitor.first_name} {visitor.last_name}",
        'visitor_company': visitor.company or '',
        'visitor_purpose': checkin.purpose or '',
        'host_name': f"{host.first_name} {host.last_name}" if host else 'N/A',
        'check_in_date': checkin.check_in_time.strftime('%Y-%m-%d'),
        'check_in_time': checkin.check_in_time.strftime('%H:%M')
    }
    
    # Replace placeholders in template elements
    for element in template.get('elements', []):
        if element.get('type') == 'text' and 'text' in element:
            text = element['text']
            for key, value in context.items():
                placeholder = '{{' + key + '}}'
                text = text.replace(placeholder, value)
            element['text'] = text
    
    # Create a new badge record
    badge = Badge(
        check_in_id=checkin.id,
        template_data=json.dumps(template),
        created_at=datetime.utcnow()
    )
    db.session.add(badge)
    db.session.commit()
    
    return template

def create_default_email_templates(organization_id):
    """Create default email templates for a new organization"""
    templates = [
        {
            'name': 'Check-in Notification',
            'subject': 'Visitor Check-in: {{visitor_name}} has arrived',
            'body': """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Visitor Check-in Notification</h2>
                    <p>Hello,</p>
                    <p>A visitor has checked in to see you:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Name:</strong> {{visitor_name}}</p>
                        <p><strong>Company:</strong> {{visitor_company}}</p>
                        <p><strong>Purpose:</strong> {{visitor_purpose}}</p>
                        <p><strong>Check-in Time:</strong> {{check_in_time}}</p>
                    </div>
                    <p>Please greet your visitor at the reception area.</p>
                    <p>Thank you,<br>{{organization_name}} Visitor Management System</p>
                </div>
            """,
            'template_type': 'check_in'
        },
        {
            'name': 'Check-out Notification',
            'subject': 'Visitor Check-out: {{visitor_name}} has departed',
            'body': """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Visitor Check-out Notification</h2>
                    <p>Hello,</p>
                    <p>Your visitor has checked out:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Name:</strong> {{visitor_name}}</p>
                        <p><strong>Company:</strong> {{visitor_company}}</p>
                        <p><strong>Purpose:</strong> {{visitor_purpose}}</p>
                        <p><strong>Check-in Time:</strong> {{check_in_time}}</p>
                        <p><strong>Check-out Time:</strong> {{check_out_time}}</p>
                        <p><strong>Duration:</strong> {{duration}}</p>
                    </div>
                    <p>Thank you,<br>{{organization_name}} Visitor Management System</p>
                </div>
            """,
            'template_type': 'check_out'
        },
        {
            'name': 'Preregistration Confirmation',
            'subject': 'Visitor Preregistration: {{visitor_name}} on {{expected_arrival}}',
            'body': """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Visitor Preregistration Confirmation</h2>
                    <p>Hello,</p>
                    <p>A visitor has been preregistered to meet you:</p>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Name:</strong> {{visitor_name}}</p>
                        <p><strong>Company:</strong> {{visitor_company}}</p>
                        <p><strong>Purpose:</strong> {{visitor_purpose}}</p>
                        <p><strong>Expected Arrival:</strong> {{expected_arrival}}</p>
                    </div>
                    <p>You will be notified when the visitor checks in.</p>
                    <p>Thank you,<br>{{organization_name}} Visitor Management System</p>
                </div>
            """,
            'template_type': 'preregister'
        }
    ]
    
    for template_data in templates:
        template = EmailTemplate(
            organization_id=organization_id,
            name=template_data['name'],
            subject=template_data['subject'],
            body=template_data['body'],
            template_type=template_data['template_type'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(template)
    
    db.session.commit()

def create_default_badge_template(organization_id):
    """Create default badge template for a new organization"""
    organization = Organization.query.get(organization_id)
    
    default_template = {
        'layout': 'portrait',
        'width': '3.5in',
        'height': '2in',
        'elements': [
            {
                'type': 'text',
                'x': '50%',
                'y': '15%',
                'align': 'center',
                'text': organization.name,
                'fontSize': '16pt',
                'fontWeight': 'bold'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '25%',
                'align': 'center',
                'text': 'VISITOR',
                'fontSize': '14pt'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '40%',
                'align': 'center',
                'text': '{{visitor_name}}',
                'fontSize': '18pt',
                'fontWeight': 'bold'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '50%',
                'align': 'center',
                'text': '{{visitor_company}}',
                'fontSize': '12pt'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '60%',
                'align': 'center',
                'text': 'Visiting: {{host_name}}',
                'fontSize': '12pt'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '70%',
                'align': 'center',
                'text': '{{check_in_date}}',
                'fontSize': '12pt'
            },
            {
                'type': 'text',
                'x': '50%',
                'y': '85%',
                'align': 'center',
                'text': 'Please return badge upon departure',
                'fontSize': '10pt'
            }
        ]
    }
    
    organization.badge_template = json.dumps(default_template)
    db.session.commit()

def log_action(event_type, event_data=None):
    """Log an action in the system"""
    if not current_user or not current_user.is_authenticated:
        return
    
    log = Log(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type=event_type,
        event_data=json.dumps(event_data) if event_data else None,
        created_at=datetime.utcnow()
    )
    
    db.session.add(log)
    db.session.commit()