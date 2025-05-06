# Visitor Management System Database Schema Documentation

This document provides a comprehensive overview of the database schema used in the Visitor Management System. The system is built with Flask and SQLAlchemy, using PostgreSQL as the database backend.

## Overview

The database consists of 11 tables designed to manage organizations, users, staff, visitors, check-ins, and other critical components of the visitor management process.

## Entity Relationship Diagram (ERD)

```
[organizations] 1---* [users]
[organizations] 1---* [staff]
[organizations] 1---* [visitors]
[organizations] 1---* [email_templates]
[organizations] 1---* [documents]
[organizations] 1---* [subscriptions]
[organizations] 1---* [settings]
[organizations] 1---* [logs]
[visitors] 1---* [checkins]
[staff] 1---* [checkins]
[checkins] 1---* [badges]
[staff] 1---* [preregistered_visitors]
[users] 1---* [logs]
```

## Table Descriptions

### Organizations

The central entity that represents companies or institutions using the system.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | Organization name |
| created_at | TIMESTAMP | Creation timestamp |
| logo | TEXT | Base64 encoded logo |
| primary_color | VARCHAR(20) | Primary brand color |
| secondary_color | VARCHAR(20) | Secondary brand color |
| contact_email | VARCHAR(120) | Main contact email |
| contact_phone | VARCHAR(20) | Main contact phone |
| address | TEXT | Physical address |
| badge_template | TEXT | JSON string for badge template |
| subscription_plan | VARCHAR(50) | Current subscription plan |
| subscription_status | VARCHAR(20) | Subscription status |
| subscription_expires_at | TIMESTAMP | Subscription expiration date |
| stripe_customer_id | VARCHAR(100) | Stripe customer ID |
| enable_photo_capture | BOOLEAN | Photo capture feature flag |
| enable_badge_printing | BOOLEAN | Badge printing feature flag |
| enable_auto_checkout | BOOLEAN | Auto checkout feature flag |
| enable_email_notifications | BOOLEAN | Email notifications feature flag |

### Users

Users who can log in to administer the system.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| username | VARCHAR(64) | Unique username |
| email | VARCHAR(120) | Unique email address |
| password_hash | VARCHAR(256) | Hashed password |
| first_name | VARCHAR(64) | First name |
| last_name | VARCHAR(64) | Last name |
| is_admin | BOOLEAN | Admin status flag |
| is_active | BOOLEAN | Account active status |
| created_at | TIMESTAMP | Creation timestamp |
| last_login | TIMESTAMP | Last login timestamp |
| organization_id | INTEGER | Foreign key to organizations |

### Staff

Staff members who can host visitors.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| first_name | VARCHAR(64) | First name |
| last_name | VARCHAR(64) | Last name |
| email | VARCHAR(120) | Email address |
| phone | VARCHAR(20) | Phone number |
| department | VARCHAR(64) | Department name |
| position | VARCHAR(64) | Job position/title |
| photo | TEXT | Base64 encoded photo |
| organization_id | INTEGER | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |

### Visitors

People who visit the organization.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| first_name | VARCHAR(64) | First name |
| last_name | VARCHAR(64) | Last name |
| email | VARCHAR(120) | Email address |
| phone | VARCHAR(20) | Phone number |
| company | VARCHAR(100) | Visitor's company |
| purpose | VARCHAR(200) | Purpose of visit |
| photo | TEXT | Base64 encoded photo |
| organization_id | INTEGER | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |

### Check-ins

Records of visitor check-ins and check-outs.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| visitor_id | INTEGER | Foreign key to visitors |
| staff_id | INTEGER | Foreign key to staff (host) |
| check_in_time | TIMESTAMP | Check-in timestamp |
| check_out_time | TIMESTAMP | Check-out timestamp |
| badge_printed | BOOLEAN | Badge printed flag |
| is_active | BOOLEAN | Active visit flag |
| purpose | VARCHAR(200) | Purpose of visit |
| notes | TEXT | Additional notes |

### Badges

Records of visitor badges.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| check_in_id | INTEGER | Foreign key to checkins |
| template_data | TEXT | JSON string with badge data |
| created_at | TIMESTAMP | Creation timestamp |
| printed_at | TIMESTAMP | Print timestamp |

### Email Templates

Templates for email notifications.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | Template name |
| subject | VARCHAR(200) | Email subject line |
| body | TEXT | Email body (HTML) |
| template_type | VARCHAR(50) | Template type |
| organization_id | INTEGER | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### Documents

Legal documents for visitor acceptance.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | Document name |
| content | TEXT | Document content |
| document_type | VARCHAR(50) | Document type |
| organization_id | INTEGER | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### Subscriptions

Organization subscription details.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| organization_id | INTEGER | Foreign key to organizations |
| plan_name | VARCHAR(50) | Subscription plan name |
| status | VARCHAR(20) | Subscription status |
| stripe_subscription_id | VARCHAR(100) | Stripe subscription ID |
| start_date | TIMESTAMP | Start date |
| end_date | TIMESTAMP | End date |
| price | FLOAT | Subscription price |
| features | TEXT | JSON string of features |

### Preregistered Visitors

Visitors scheduled for future visits.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| first_name | VARCHAR(64) | First name |
| last_name | VARCHAR(64) | Last name |
| email | VARCHAR(120) | Email address |
| phone | VARCHAR(20) | Phone number |
| company | VARCHAR(100) | Visitor's company |
| purpose | VARCHAR(200) | Purpose of visit |
| expected_arrival | TIMESTAMP | Expected arrival time |
| staff_id | INTEGER | Foreign key to staff (host) |
| organization_id | INTEGER | Foreign key to organizations |
| created_at | TIMESTAMP | Creation timestamp |
| status | VARCHAR(20) | Status (pending, checked_in, cancelled) |

### Settings

Organization-specific settings.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| organization_id | INTEGER | Foreign key to organizations |
| key | VARCHAR(100) | Setting key |
| value | TEXT | Setting value |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### Logs

System activity logs.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| organization_id | INTEGER | Foreign key to organizations |
| user_id | INTEGER | Foreign key to users |
| event_type | VARCHAR(50) | Type of event |
| event_data | TEXT | JSON string with event details |
| created_at | TIMESTAMP | Creation timestamp |

## Indexes

The schema includes optimized indexes for frequently queried columns:

- Organizations: name
- Users: username, email
- Staff: organization_id
- Visitors: organization_id
- Check-ins: visitor_id, staff_id, is_active
- Email Templates: organization_id + template_type
- Preregistered Visitors: status, expected_arrival
- Logs: organization_id, event_type
- Settings: organization_id + key

## Relationships and Constraints

The database uses foreign key constraints to ensure data integrity:

- Each user, staff, visitor, email template, document, and setting belongs to an organization
- Each check-in is associated with a visitor and optionally a staff member
- Each badge is associated with a check-in
- Each preregistered visitor is associated with a staff member and organization
- Each log entry is associated with an organization and optionally a user

## Database Initialization

The database is automatically initialized when the application starts. The `db_setup.py` script can be used to create initial data including:

- A default organization
- An admin user (username: admin@example.com, password: admin123)
- Default email templates for visitor check-in, check-out, and preregistration

## Schema Modifications

To modify the schema:

1. Update the relevant model class in `app/models.py`
2. Run database migrations if using a migration tool, or restart the application to apply changes automatically via `db.create_all()`