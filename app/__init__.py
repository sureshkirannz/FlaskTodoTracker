import os
import logging
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the DeclarativeBase
db = SQLAlchemy(model_class=Base)

# Initialize LoginManager for user sessions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Initialize Flask-Mail
mail = Mail()

# Initialize CSRF protection
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration from environment variables or use defaults
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_for_testing'),
        WTF_CSRF_SECRET_KEY=os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf_key_for_forms'),
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,  # 1 hour
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'postgresql://postgres:1234567@159.13.60.81:5432/VisitorManagement'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_recycle": 300,
            "pool_pre_ping": True,
        },
        # Mail settings
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'localhost'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 25)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', '1', 't'),
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't'),
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
        # Application settings
        APP_NAME='Visitor Management System',
        ADMIN_EMAIL=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max upload size
    )
    
    # Configure logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from app import models
        
        # Create database tables if they don't exist
        db.create_all()
        
        # Register blueprints
        from app.routes.auth import auth
        app.register_blueprint(auth)
        
        from app.routes.dashboard import dashboard
        app.register_blueprint(dashboard)
        
        from app.routes.visitor import visitor
        app.register_blueprint(visitor)
        
        from app.routes.staff import staff
        app.register_blueprint(staff)
        
        from app.routes.reports import reports
        app.register_blueprint(reports)
        
        from app.routes.settings import settings
        app.register_blueprint(settings)
        
        from app.routes.kiosk import kiosk
        app.register_blueprint(kiosk)
        
        from app.routes.subscription import subscription
        app.register_blueprint(subscription)
    
    # Register template filters
    @app.template_filter('format_datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        """Format a datetime object to string."""
        if value is None:
            return ""
        return value.strftime(format)
    
    # Add utility functions to template context
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        def now():
            return datetime.utcnow()
        
        return dict(now=now)
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    # Define the root route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app