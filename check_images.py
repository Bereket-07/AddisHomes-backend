import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.repository.mysql_repo import MySQLRealEstateRepository

async def check_images():
    """Check if images exist in the database"""
    repo = MySQLRealEstateRepository()
    
    try:
        # Check if images table exists and has data
        query = "SELECT image_id, content_type, LENGTH(data) as size FROM images LIMIT 10"
        results = await repo._execute_query(query, fetch_all=True)
        
        if results:
            print(f"Found {len(results)} images in database:")
            for img in results:
                print(f"  - ID: {img['image_id']}, Type: {img['content_type']}, Size: {img['size']} bytes")
        else:
            print("No images found in database!")
            
        # Check property_images table
        query2 = "SELECT property_id, image_url FROM property_images LIMIT 10"
        prop_images = await repo._execute_query(query2, fetch_all=True)
        
        if prop_images:
            print(f"\nFound {len(prop_images)} property image references:")
            for img in prop_images:
                print(f"  - Property: {img['property_id']}, URL: {img['image_url']}")
        else:
            print("\nNo property image references found!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await repo.close()

if __name__ == "__main__":
    asyncio.run(check_images())
