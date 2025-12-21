#!/usr/bin/env python3
"""
Test script to verify MySQL connection and basic functionality (Synchronous)
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
from src.domain.models.user_models import UserCreate, UserRole
from src.domain.models.property_models import PropertyCreate, PropertyType, Location
from src.utils.config import settings

load_dotenv()

def test_mysql_connection():
    """Test MySQL connection and basic operations"""
    print("Testing MySQL connection (SYNC)...")
    
    try:
        # Initialize repository
        repo = MySQLRealEstateRepository()
        
        # Test 1: Create a test user
        print("1. Testing user creation...")
        test_user = UserCreate(
            phone_number="+251911000000",
            telegram_id=123456789,
            display_name="Test User",
            language="en",
            roles=[UserRole.BUYER]
        )
        
        created_user = repo.create_user(test_user)
        print(f"✓ User created: {created_user.uid}")
        
        # Test 2: Retrieve user
        print("2. Testing user retrieval...")
        retrieved_user = repo.get_user_by_id(created_user.uid)
        print(f"✓ User retrieved: {retrieved_user.display_name}")
        
        # Test 3: Create a test property
        print("3. Testing property creation...")
        test_property = PropertyCreate(
            property_type=PropertyType.APARTMENT,
            location=Location(
                region="Addis Ababa",
                city="Addis Ababa",
                site="Bole"
            ),
            bedrooms=2,
            bathrooms=1,
            size_sqm=80.0,
            price_etb=2500000.0,
            description="Test property for MySQL testing",
            image_urls=["https://example.com/image1.jpg"],
            broker_id=created_user.uid,
            broker_name="Test Broker",
            broker_phone="+251911000000"
        )
        
        created_property = repo.create_property(test_property)
        print(f"✓ Property created: {created_property.pid}")
        
        # Test 4: Query properties
        print("4. Testing property query...")
        from src.domain.models.property_models import PropertyFilter
        filter_obj = PropertyFilter()
        properties = repo.query_properties(filter_obj)
        print(f"✓ Found {len(properties)} properties")
        
        # Test 5: Test user roles
        print("5. Testing user roles...")
        repo.set_user_role(created_user.uid, UserRole.BROKER, True)
        updated_user = repo.get_user_by_id(created_user.uid)
        print(f"✓ User roles updated: {[role.value for role in updated_user.roles]}")
        
        # Test 6: Clean up test data
        print("6. Cleaning up test data...")
        repo.delete_property(created_property.pid)
        repo.delete_user(created_user.uid)
        print("✓ Test data cleaned up")
        
        print("\n🎉 All MySQL tests passed! Your database is ready to use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your MySQL connection settings in .env")
        print("2. Ensure the database schema has been imported")
        print("3. Verify your cPanel MySQL credentials")
        print("4. Check that the MySQL service is running")
        raise
    finally:
        # Sync repo doesn't strictly need close() in this simple script context
        pass

if __name__ == "__main__":
    print("MySQL Connection Test")
    print("=" * 50)
    print(f"Database Type: {settings.DATABASE_TYPE}")
    print(f"MySQL Host: {settings.MYSQL_HOST}")
    print(f"MySQL Database: {settings.MYSQL_DATABASE}")
    print(f"MySQL User: {settings.MYSQL_USER}")
    print("=" * 50)
    
    test_mysql_connection()
