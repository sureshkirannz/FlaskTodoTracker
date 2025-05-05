import jwt
from time import time
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database."""
    return User.query.get(int(user_id))

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logo = db.Column(db.Text, nullable=True)  # Base64 encoded logo
    primary_color = db.Column(db.String(20), default="#007bff")
    secondary_color = db.Column(db.String(20), default="#6c757d")
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Badge template for printing visitor badges
    badge_template = db.Column(db.Text, nullable=True)  # JSON string for badge template
    
    # Subscription information
    subscription_plan = db.Column(db.String(50), default="free")
    subscription_status = db.Column(db.String(20), default="active")
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    
    # Feature flags
    enable_photo_capture = db.Column(db.Boolean, default=True)
    enable_badge_printing = db.Column(db.Boolean, default=True)
    enable_auto_checkout = db.Column(db.Boolean, default=True)
    enable_email_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    visitors = db.relationship('Visitor', backref='organization', lazy=True)
    staff = db.relationship('Staff', backref='organization', lazy=True)
    email_templates = db.relationship('EmailTemplate', backref='organization', lazy=True)
    documents = db.relationship('Document', backref='organization', lazy=True)
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    def set_password(self, password):
        """Set password hash from plain text password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if plain text password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        """Generate a password reset token."""
        secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            secret_key,
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        """Verify a password reset token."""
        secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
        try:
            id = jwt.decode(
                token,
                secret_key,
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Staff(db.Model):
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(64), nullable=True)
    position = db.Column(db.String(64), nullable=True)
    photo = db.Column(db.Text, nullable=True)  # Base64 encoded photo
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Staff {self.first_name} {self.last_name}>'

class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    purpose = db.Column(db.String(200), nullable=True)
    photo = db.Column(db.Text, nullable=True)  # Base64 encoded photo
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    checkins = db.relationship('CheckIn', backref='visitor', lazy=True)
    
    def __repr__(self):
        return f'<Visitor {self.first_name} {self.last_name}>'

class CheckIn(db.Model):
    __tablename__ = 'checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitors.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    badge_printed = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    purpose = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    host = db.relationship('Staff', backref='hosting', lazy=True)
    
    def __repr__(self):
        return f'<CheckIn {self.visitor_id} at {self.check_in_time}>'

class Badge(db.Model):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    check_in_id = db.Column(db.Integer, db.ForeignKey('checkins.id'), nullable=False)
    template_data = db.Column(db.Text, nullable=False)  # JSON string with badge data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    printed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    check_in = db.relationship('CheckIn', backref='badge', lazy=True)
    
    def __repr__(self):
        return f'<Badge {self.id} for CheckIn {self.check_in_id}>'

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # e.g. check_in, check_out
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Could be PDF content as base64 or HTML content
    document_type = db.Column(db.String(50), nullable=False)  # e.g. nda, policy, waiver
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.name}>'

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    plan_name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.Text, nullable=True)  # JSON string of features
    
    # Relationships
    organization = db.relationship('Organization', backref='subscriptions', lazy=True)
    
    def __repr__(self):
        return f'<Subscription {self.plan_name} for Organization {self.organization_id}>'

class PreregisteredVisitor(db.Model):
    __tablename__ = 'preregistered_visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    purpose = db.Column(db.String(200), nullable=True)
    expected_arrival = db.Column(db.DateTime, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")  # pending, checked_in, cancelled
    
    # Relationships
    host = db.relationship('Staff', backref='preregistered_visitors', lazy=True)
    
    def __repr__(self):
        return f'<PreregisteredVisitor {self.first_name} {self.last_name}>'

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='settings', lazy=True)
    
    def __repr__(self):
        return f'<Setting {self.key} for Organization {self.organization_id}>'

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.Text, nullable=True)  # JSON string with event details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='logs', lazy=True)
    user = db.relationship('User', backref='logs', lazy=True)
    
    def __repr__(self):
        return f'<Log {self.event_type} at {self.created_at}>'