from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
import asyncio
from src.utils.config import settings

def check_data():
    print(f"Checking database: {settings.MYSQL_DATABASE} on {settings.MYSQL_HOST}")
    repo = MySQLRealEstateRepository()
    
    try:
        # Count Users
        users = repo.list_users()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f" - {u.display_name} ({u.phone_number}) Role: {[r.value for r in u.roles]}")

        # Count Properties
        # queries default to APPROVED, so let's check status count specifically
        status_counts = repo.count_properties_by_status()
        print("\nProperty Counts by Status:")
        total_props = 0
        for status, count in status_counts.items():
            print(f" - {status.value}: {count}")
            total_props += count
            
        if total_props == 0:
            print("⚠️  No properties found in database.")

        # Count Cars
        car_counts = repo.count_cars_by_status()
        print("\nCar Counts by Status:")
        total_cars = 0
        for status, count in car_counts.items():
            print(f" - {status.value}: {count}")
            total_cars += count

    except Exception as e:
        print(f"Error checking data: {e}")
    finally:
        repo.close()

if __name__ == "__main__":
    check_data()
