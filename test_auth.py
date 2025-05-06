"""
Test authentication-related functions directly.
"""
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
import sys

# Get DB URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Connecting to: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
session = Session(engine)

def check_user_password(email, password):
    """Test user password verification with direct SQL queries."""
    # Get the user with the specified email
    query = text(f"SELECT id, username, email, password_hash FROM users WHERE email = :email")
    result = session.execute(query, {"email": email}).fetchone()
    
    if not result:
        print(f"No user found with email: {email}")
        return False
    
    user_id, username, user_email, password_hash = result
    print(f"Found user: ID={user_id}, Username={username}, Email={user_email}")
    
    # Verify the password
    if password_hash is None:
        print("WARNING: User has no password hash!")
        return False
    
    is_valid = check_password_hash(password_hash, password)
    if is_valid:
        print("Password is valid!")
    else:
        print("Password is NOT valid!")
    
    return is_valid

def create_test_user(username, email, password):
    """Create a test user with a valid password hash."""
    # Check if user already exists
    query = text("SELECT id FROM users WHERE email = :email OR username = :username")
    result = session.execute(query, {"email": email, "username": username}).fetchone()
    
    if result:
        print(f"User already exists with ID: {result[0]}")
        return False
    
    # Create the password hash
    password_hash = generate_password_hash(password)
    
    # Get organization to use
    org_query = text("SELECT id FROM organizations LIMIT 1")
    org_result = session.execute(org_query).fetchone()
    
    if not org_result:
        print("No organizations found!")
        return False
    
    org_id = org_result[0]
    
    # Insert the new user
    insert_query = text("""
    INSERT INTO users (username, email, password_hash, is_admin, organization_id)
    VALUES (:username, :email, :password_hash, true, :org_id)
    RETURNING id
    """)
    
    try:
        result = session.execute(insert_query, {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "org_id": org_id
        })
        session.commit()
        new_id = result.fetchone()[0]
        print(f"Created new user with ID: {new_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error creating user: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_auth.py check <email> <password>")
        print("  python test_auth.py create <username> <email> <password>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check" and len(sys.argv) == 4:
        email = sys.argv[2]
        password = sys.argv[3]
        check_user_password(email, password)
    
    elif command == "create" and len(sys.argv) == 5:
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        create_test_user(username, email, password)
    
    else:
        print("Invalid command or arguments")
        print("Usage:")
        print("  python test_auth.py check <email> <password>")
        print("  python test_auth.py create <username> <email> <password>")