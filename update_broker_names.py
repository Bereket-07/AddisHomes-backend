"""
Script to update broker names in properties and cars tables.
Run this after updating a user's display_name to sync all their listings.
"""
from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
from src.utils.config import settings

def update_broker_names(old_name: str, new_name: str):
    """
    Update broker_name from old_name to new_name in both properties and cars tables.
    
    Args:
        old_name: The old broker name to replace (e.g., "Dere Birhanu")
        new_name: The new broker name to use
    """
    repo = MySQLRealEstateRepository()
    
    try:
        conn = repo.get_connection()
        cursor = conn.cursor()
        
        # Update properties table
        properties_query = """
            UPDATE properties 
            SET broker_name = %s 
            WHERE broker_name = %s
        """
        cursor.execute(properties_query, (new_name, old_name))
        properties_updated = cursor.rowcount
        
        # Update cars table
        cars_query = """
            UPDATE cars 
            SET broker_name = %s 
            WHERE broker_name = %s
        """
        cursor.execute(cars_query, (new_name, old_name))
        cars_updated = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Successfully updated broker names:")
        print(f"   - Properties: {properties_updated} records updated")
        print(f"   - Cars: {cars_updated} records updated")
        print(f"   - Changed from: '{old_name}' to '{new_name}'")
        
    except Exception as e:
        print(f"❌ Error updating broker names: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        repo.close()

if __name__ == "__main__":
    # INSTRUCTIONS:
    # 1. Update the values below with the old and new broker names
    # 2. Run: python update_broker_names.py
    
    OLD_BROKER_NAME = "Dere Birhanu"  # Change this to the old name
    NEW_BROKER_NAME = "Your New Name Here"  # Change this to the new name
    
    print(f"About to update broker names:")
    print(f"  FROM: '{OLD_BROKER_NAME}'")
    print(f"  TO:   '{NEW_BROKER_NAME}'")
    print()
    
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() == 'yes':
        update_broker_names(OLD_BROKER_NAME, NEW_BROKER_NAME)
    else:
        print("Operation cancelled.")
