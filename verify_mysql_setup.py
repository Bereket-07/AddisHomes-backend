#!/usr/bin/env python3
"""
Verify that your application is properly configured for MySQL
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import settings
from src.infrastructure.repository.database_factory import get_database_repository

load_dotenv()

def verify_setup():
    """Verify MySQL setup and configuration"""
    print("MySQL Setup Verification")
    print("=" * 50)
    
    # Check database type
    print(f"Database Type: {settings.DATABASE_TYPE}")
    if settings.DATABASE_TYPE.lower() != "mysql":
        print("⚠️  WARNING: DATABASE_TYPE is not set to 'mysql'")
        print("   Your application will use Firestore instead of MySQL")
        return False
    
    # Check MySQL configuration
    print(f"MySQL Host: {settings.MYSQL_HOST}")
    print(f"MySQL Port: {settings.MYSQL_PORT}")
    print(f"MySQL Database: {settings.MYSQL_DATABASE}")
    print(f"MySQL User: {settings.MYSQL_USER}")
    print(f"MySQL Password: {'*' * len(settings.MYSQL_PASSWORD) if settings.MYSQL_PASSWORD else 'NOT SET'}")
    
    # Check if repository factory works
    try:
        repo = get_database_repository()
        repo_type = type(repo).__name__
        print(f"Repository Type: {repo_type}")
        
        if "MySQL" in repo_type:
            print("✅ MySQL repository is active")
        else:
            print("⚠️  WARNING: Not using MySQL repository")
            return False
            
    except Exception as e:
        print(f"❌ Error creating repository: {e}")
        return False
    
    # Check required environment variables
    required_vars = [
        "MYSQL_HOST", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n✅ All checks passed! Your application is configured for MySQL")
    return True

if __name__ == "__main__":
    success = verify_setup()
    
    if success:
        print("\n🎉 Your system is ready to use MySQL!")
        print("\nTo start your application:")
        print("python src/app/main.py")
    else:
        print("\n❌ Please fix the issues above before proceeding")
        print("\nMake sure your .env file has the correct MySQL settings")
