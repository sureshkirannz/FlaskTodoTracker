"""
Check for existing tables in the database.
"""
import os
from sqlalchemy import create_engine, inspect

# Get DB URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Connecting to: {DATABASE_URL}")

# Create engine
engine = create_engine(DATABASE_URL)

# Get inspector
inspector = inspect(engine)

# Get all table names
table_names = inspector.get_table_names()

print(f"Found {len(table_names)} tables in the database:")
for table_name in table_names:
    print(f"- {table_name}")

# Check if our application tables exist
required_tables = [
    'organizations', 
    'users', 
    'staff', 
    'visitors', 
    'visits',
    'email_templates',
    'badge_templates',
    'documents'
]

missing_tables = [table for table in required_tables if table not in table_names]

if missing_tables:
    print("\nMissing required tables:")
    for table in missing_tables:
        print(f"- {table}")
else:
    print("\nAll required tables exist.")