#!/usr/bin/env python3
"""
Migration script to move data from Firestore to MySQL
Run this script after setting up your MySQL database
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.repository.firestore_repo import RealEstateRepository
from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
from src.utils.config import settings

load_dotenv()

async def migrate_data():
    """Migrate data from Firestore to MySQL"""
    print("Starting migration from Firestore to MySQL...")
    
    # Initialize repositories
    firestore_repo = RealEstateRepository()
    mysql_repo = MySQLRealEstateRepository()
    
    try:
        # Migrate users
        print("Migrating users...")
        users = await firestore_repo.list_users()
        migrated_users = 0
        
        for user in users:
            try:
                # Check if user already exists in MySQL
                existing_user = await mysql_repo.get_user_by_phone_number(user.phone_number)
                if not existing_user:
                    # Create user in MySQL
                    user_create_data = {
                        "phone_number": user.phone_number,
                        "telegram_id": user.telegram_id,
                        "display_name": user.display_name,
                        "language": user.language,
                        "roles": user.roles,
                        "password": None  # We'll handle passwords separately
                    }
                    await mysql_repo.create_user(user_create_data)
                    migrated_users += 1
                    print(f"Migrated user: {user.phone_number}")
                else:
                    print(f"User already exists: {user.phone_number}")
            except Exception as e:
                print(f"Error migrating user {user.phone_number}: {e}")
        
        print(f"Migrated {migrated_users} users")
        
        # Migrate properties
        print("Migrating properties...")
        all_properties = await firestore_repo.get_properties_by_status("approved")
        all_properties.extend(await firestore_repo.get_properties_by_status("pending"))
        all_properties.extend(await firestore_repo.get_properties_by_status("rejected"))
        all_properties.extend(await firestore_repo.get_properties_by_status("sold"))
        
        migrated_properties = 0
        for property in all_properties:
            try:
                # Check if property already exists in MySQL
                try:
                    existing_property = await mysql_repo.get_property_by_id(property.pid)
                    print(f"Property already exists: {property.pid}")
                    continue
                except:
                    pass  # Property doesn't exist, continue with migration
                
                # Create property in MySQL
                property_create_data = {
                    "property_type": property.property_type,
                    "location": property.location,
                    "bedrooms": property.bedrooms,
                    "bathrooms": property.bathrooms,
                    "size_sqm": property.size_sqm,
                    "price_etb": property.price_etb,
                    "description": property.description,
                    "image_urls": property.image_urls,
                    "furnishing_status": property.furnishing_status,
                    "condominium_scheme": property.condominium_scheme,
                    "floor_level": property.floor_level,
                    "debt_status": property.debt_status,
                    "structure_type": property.structure_type,
                    "plot_size_sqm": property.plot_size_sqm,
                    "title_deed": property.title_deed,
                    "kitchen_type": property.kitchen_type,
                    "living_rooms": property.living_rooms,
                    "water_tank": property.water_tank,
                    "parking_spaces": property.parking_spaces,
                    "is_commercial": property.is_commercial,
                    "total_floors": property.total_floors,
                    "total_units": property.total_units,
                    "has_elevator": property.has_elevator,
                    "has_private_rooftop": property.has_private_rooftop,
                    "is_two_story_penthouse": property.is_two_story_penthouse,
                    "has_private_entrance": property.has_private_entrance,
                    "broker_id": property.broker_id,
                    "broker_name": property.broker_name,
                    "broker_phone": property.broker_phone
                }
                
                # Create the property
                new_property = await mysql_repo.create_property(property_create_data)
                
                # Update status and other fields
                await mysql_repo.update_property(property.pid, {
                    "status": property.status.value,
                    "rejection_reason": property.rejection_reason
                })
                
                migrated_properties += 1
                print(f"Migrated property: {property.pid}")
                
            except Exception as e:
                print(f"Error migrating property {property.pid}: {e}")
        
        print(f"Migrated {migrated_properties} properties")
        
        # Migrate cars
        print("Migrating cars...")
        all_cars = await firestore_repo.list_all_cars()
        
        migrated_cars = 0
        for car in all_cars:
            try:
                # Check if car already exists in MySQL
                try:
                    existing_car = await mysql_repo.get_car_by_id(car.cid)
                    print(f"Car already exists: {car.cid}")
                    continue
                except:
                    pass  # Car doesn't exist, continue with migration
                
                # Create car in MySQL
                car_create_data = {
                    "car_type": car.car_type,
                    "price_etb": car.price_etb,
                    "images": car.images,
                    "manufacturer": car.manufacturer,
                    "model_name": car.model_name,
                    "model_year": car.model_year,
                    "color": car.color,
                    "plate": car.plate,
                    "engine": car.engine,
                    "power_hp": car.power_hp,
                    "transmission": car.transmission,
                    "fuel_efficiency_kmpl": car.fuel_efficiency_kmpl,
                    "motor_type": car.motor_type,
                    "mileage_km": car.mileage_km,
                    "description": car.description,
                    "broker_id": car.broker_id,
                    "broker_name": car.broker_name,
                    "broker_phone": car.broker_phone
                }
                
                # Create the car
                new_car = await mysql_repo.create_car(car_create_data)
                
                # Update status
                await mysql_repo.update_car_status(car.cid, car.status)
                
                migrated_cars += 1
                print(f"Migrated car: {car.cid}")
                
            except Exception as e:
                print(f"Error migrating car {car.cid}: {e}")
        
        print(f"Migrated {migrated_cars} cars")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        # Close connections
        if hasattr(mysql_repo, 'close'):
            await mysql_repo.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
