#!/usr/bin/env python3
"""
Script to set up fresh MySQL database with initial data
Use this instead of migration if you want to start fresh
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
from src.domain.models.user_models import UserCreate, UserRole
from src.domain.models.property_models import PropertyCreate, PropertyType, Location
from src.utils.config import settings

load_dotenv()

async def setup_fresh_database():
    """Set up fresh MySQL database with initial admin user"""
    print("Setting up fresh MySQL database...")
    
    try:
        repo = MySQLRealEstateRepository()
        
        # Create initial admin user
        print("Creating initial admin user...")
        admin_user = UserCreate(
            phone_number=settings.ADMIN_PHONE_NUMBER,
            telegram_id=0,  # Will be updated when admin links Telegram
            display_name="System Administrator",
            language="en",
            roles=[UserRole.ADMIN]
        )
        
        try:
            # Check if admin already exists
            existing_admin = await repo.get_user_by_phone_number(settings.ADMIN_PHONE_NUMBER)
            if existing_admin:
                print(f"✓ Admin user already exists: {existing_admin.uid}")
            else:
                created_admin = await repo.create_user(admin_user)
                print(f"✓ Admin user created: {created_admin.uid}")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create a sample broker user for testing
        print("Creating sample broker user...")
        broker_user = UserCreate(
            phone_number="+251911000001",
            telegram_id=0,
            display_name="Sample Broker",
            language="en",
            roles=[UserRole.BROKER]
        )
        
        try:
            existing_broker = await repo.get_user_by_phone_number("+251911000001")
            if not existing_broker:
                created_broker = await repo.create_user(broker_user)
                print(f"✓ Sample broker created: {created_broker.uid}")
            else:
                print("✓ Sample broker already exists")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create a sample property for testing
        print("Creating sample property...")
        sample_property = PropertyCreate(
            property_type=PropertyType.APARTMENT,
            location=Location(
                region="Addis Ababa",
                city="Addis Ababa", 
                site="Bole"
            ),
            bedrooms=2,
            bathrooms=1,
            size_sqm=85.0,
            price_etb=3000000.0,
            description="Beautiful 2-bedroom apartment in Bole with modern amenities. Perfect for families looking for comfort and convenience.",
            image_urls=[
                "https://example.com/sample1.jpg",
                "https://example.com/sample2.jpg"
            ],
            broker_id=None,  # Will be set when broker submits
            broker_name="Sample Broker",
            broker_phone="+251911000001"
        )
        
        try:
            created_property = await repo.create_property(sample_property)
            print(f"✓ Sample property created: {created_property.pid}")
        except Exception as e:
            print(f"Note: {e}")
        
        print("\n🎉 Fresh MySQL database setup completed!")
        print("\nNext steps:")
        print("1. Your system is now running on MySQL")
        print("2. Admin user is ready (phone: " + settings.ADMIN_PHONE_NUMBER + ")")
        print("3. You can start using the system immediately")
        print("4. Users can register and submit properties")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        raise
    finally:
        if 'repo' in locals() and hasattr(repo, 'close'):
            await repo.close()

if __name__ == "__main__":
    print("Fresh MySQL Database Setup")
    print("=" * 50)
    print(f"Database: {settings.MYSQL_DATABASE}")
    print(f"Admin Phone: {settings.ADMIN_PHONE_NUMBER}")
    print("=" * 50)
    
    asyncio.run(setup_fresh_database())
