-- Visitor Management System Database Schema
-- Generated from SQLAlchemy models

-- Organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logo TEXT,
    primary_color VARCHAR(20) DEFAULT '#007bff',
    secondary_color VARCHAR(20) DEFAULT '#6c757d',
    contact_email VARCHAR(120),
    contact_phone VARCHAR(20),
    address TEXT,
    badge_template TEXT,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(20) DEFAULT 'active',
    subscription_expires_at TIMESTAMP,
    stripe_customer_id VARCHAR(100),
    enable_photo_capture BOOLEAN DEFAULT TRUE,
    enable_badge_printing BOOLEAN DEFAULT TRUE,
    enable_auto_checkout BOOLEAN DEFAULT TRUE,
    enable_email_notifications BOOLEAN DEFAULT TRUE
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id)
);

-- Staff table
CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(64),
    position VARCHAR(64),
    photo TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Visitors table
CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(120),
    phone VARCHAR(20),
    company VARCHAR(100),
    purpose VARCHAR(200),
    photo TEXT,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check-ins table
CREATE TABLE checkins (
    id SERIAL PRIMARY KEY,
    visitor_id INTEGER NOT NULL REFERENCES visitors(id),
    staff_id INTEGER REFERENCES staff(id),
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP,
    badge_printed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    purpose VARCHAR(200),
    notes TEXT
);

-- Badges table
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    check_in_id INTEGER NOT NULL REFERENCES checkins(id),
    template_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    printed_at TIMESTAMP
);

-- Email templates table
CREATE TABLE email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plan_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    stripe_subscription_id VARCHAR(100),
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    price FLOAT NOT NULL,
    features TEXT
);

-- Preregistered visitors table
CREATE TABLE preregistered_visitors (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    company VARCHAR(100),
    purpose VARCHAR(200),
    expected_arrival TIMESTAMP NOT NULL,
    staff_id INTEGER NOT NULL REFERENCES staff(id),
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Settings table
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs table
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    event_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_staff_organization ON staff(organization_id);
CREATE INDEX idx_visitors_organization ON visitors(organization_id);
CREATE INDEX idx_checkins_visitor ON checkins(visitor_id);
CREATE INDEX idx_checkins_staff ON checkins(staff_id);
CREATE INDEX idx_checkins_active ON checkins(is_active);
CREATE INDEX idx_email_templates_org_type ON email_templates(organization_id, template_type);
CREATE INDEX idx_preregistered_visitors_status ON preregistered_visitors(status);
CREATE INDEX idx_preregistered_visitors_expected_arrival ON preregistered_visitors(expected_arrival);
CREATE INDEX idx_logs_organization ON logs(organization_id);
CREATE INDEX idx_logs_event_type ON logs(event_type);
CREATE INDEX idx_settings_org_key ON settings(organization_id, key);