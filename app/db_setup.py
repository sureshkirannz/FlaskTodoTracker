"""
Database setup script for Visitor Management System.
This script initializes the database tables and creates initial admin user and organization.
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Organization, EmailTemplate

def setup_database():
    """Set up the database with initial data."""
    print("Setting up database...")
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created.")
        
        # Check if any organizations exist
        if Organization.query.first() is None:
            print("Creating default organization...")
            org = Organization(
                name="Demo Organization",
                primary_color="#007bff",
                secondary_color="#6c757d",
                contact_email="admin@example.com",
                subscription_plan="free",
                subscription_status="active",
                subscription_expires_at=datetime.utcnow() + timedelta(days=30),
                enable_photo_capture=True,
                enable_badge_printing=True,
                enable_auto_checkout=True,
                enable_email_notifications=True
            )
            db.session.add(org)
            db.session.commit()
            
            # Create admin user
            print("Creating admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                is_admin=True,
                is_active=True,
                organization_id=org.id,
                password_hash=generate_password_hash("admin123")  # Default password, change immediately
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create default email templates
            print("Creating default email templates...")
            
            # Check-in notification template
            checkin_template = EmailTemplate(
                name="Visitor Check-in Notification",
                subject="New Visitor Check-in: {{visitor.first_name}} {{visitor.last_name}}",
                body="""
                <h2>New Visitor Check-in</h2>
                <p>A new visitor has checked in to see you:</p>
                <table>
                    <tr><th>Name:</th><td>{{visitor.first_name}} {{visitor.last_name}}</td></tr>
                    <tr><th>Company:</th><td>{{visitor.company}}</td></tr>
                    <tr><th>Purpose:</th><td>{{checkin.purpose}}</td></tr>
                    <tr><th>Check-in Time:</th><td>{{checkin.check_in_time|format_datetime}}</td></tr>
                </table>
                <p>Please come to the reception area to meet your visitor.</p>
                """,
                template_type="check_in",
                organization_id=org.id
            )
            
            # Check-out notification template
            checkout_template = EmailTemplate(
                name="Visitor Check-out Notification",
                subject="Visitor Check-out: {{visitor.first_name}} {{visitor.last_name}}",
                body="""
                <h2>Visitor Check-out</h2>
                <p>A visitor has checked out:</p>
                <table>
                    <tr><th>Name:</th><td>{{visitor.first_name}} {{visitor.last_name}}</td></tr>
                    <tr><th>Company:</th><td>{{visitor.company}}</td></tr>
                    <tr><th>Check-in Time:</th><td>{{checkin.check_in_time|format_datetime}}</td></tr>
                    <tr><th>Check-out Time:</th><td>{{checkin.check_out_time|format_datetime}}</td></tr>
                    <tr><th>Total Visit Duration:</th><td>{{duration}}</td></tr>
                </table>
                """,
                template_type="check_out",
                organization_id=org.id
            )
            
            # Preregistration confirmation template
            preregister_template = EmailTemplate(
                name="Visitor Preregistration Confirmation",
                subject="Your Visit Confirmation for {{organization.name}}",
                body="""
                <h2>Visit Confirmation</h2>
                <p>Dear {{visitor.first_name}} {{visitor.last_name}},</p>
                <p>Your visit to {{organization.name}} has been confirmed:</p>
                <table>
                    <tr><th>Date/Time:</th><td>{{visitor.expected_arrival|format_datetime}}</td></tr>
                    <tr><th>Host:</th><td>{{host.first_name}} {{host.last_name}}</td></tr>
                    <tr><th>Purpose:</th><td>{{visitor.purpose}}</td></tr>
                </table>
                <p>Please arrive at our reception and check in upon arrival.</p>
                <p>Address: {{organization.address}}</p>
                """,
                template_type="preregister",
                organization_id=org.id
            )
            
            db.session.add_all([checkin_template, checkout_template, preregister_template])
            db.session.commit()
            
            print("Database setup complete!")
            print("\nDefault admin credentials:")
            print("Username: admin@example.com")
            print("Password: admin123")
            print("\nIMPORTANT: Please change the default password immediately after first login.")
        else:
            print("Database already contains data. Setup skipped.")

if __name__ == "__main__":
    setup_database()