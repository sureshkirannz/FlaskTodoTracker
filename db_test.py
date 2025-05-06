"""
Test database connection and CRUD operations.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv()

# Get DB URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Connecting to: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create a base class
Base = declarative_base()

# Define a test model
class TestUser(Base):
    __tablename__ = 'test_users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    email = Column(String(120))

# Create the test table
try:
    Base.metadata.create_all(engine)
    print("Test table created successfully")
except Exception as e:
    print(f"Error creating test table: {str(e)}")

# Try to insert a record
try:
    test_user = TestUser(name="Test User", email="test@example.com")
    session.add(test_user)
    session.commit()
    print("Test record inserted successfully")
except Exception as e:
    print(f"Error inserting test record: {str(e)}")
    session.rollback()

# Try to query the record
try:
    test_users = session.query(TestUser).all()
    print(f"Found {len(test_users)} test users")
    for user in test_users:
        print(f"  User ID: {user.id}, Name: {user.name}, Email: {user.email}")
except Exception as e:
    print(f"Error querying test records: {str(e)}")

# Clean up - drop the test table
try:
    TestUser.__table__.drop(engine)
    print("Test table dropped successfully")
except Exception as e:
    print(f"Error dropping test table: {str(e)}")

# Close the session
session.close()