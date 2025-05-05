import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_mail import Mail

# Set up logger
logger = logging.getLogger(__name__)

# Define the base model class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', '1', 't')
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Template filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        """Format a datetime object to string."""
        if value is None:
            return ""
        return value.strftime(format)
    
    # Template context processors
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        def now():
            return datetime.utcnow()
        return dict(now=now)
    
    # Import and register blueprints
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from app import models
        
        # Import and register blueprints
        from app.routes.auth import auth
        from app.routes.dashboard import dashboard
        from app.routes.visitor import visitor
        from app.routes.staff import staff
        from app.routes.settings import settings
        from app.routes.reports import reports
        from app.routes.kiosk import kiosk
        from app.routes.subscription import subscription
        
        app.register_blueprint(auth)
        app.register_blueprint(dashboard)
        app.register_blueprint(visitor)
        app.register_blueprint(staff)
        app.register_blueprint(settings)
        app.register_blueprint(reports)
        app.register_blueprint(kiosk)
        app.register_blueprint(subscription)
        
        # Create database tables if they don't exist
        db.create_all()
        
        # Initialize scheduler for tasks like auto-checkout
        from app.utils import init_scheduler
        init_scheduler(app)
    
    return app