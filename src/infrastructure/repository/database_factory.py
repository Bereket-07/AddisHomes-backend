"""
Database Factory for switching between Firestore and MySQL
"""
from src.utils.config import settings
from src.infrastructure.repository.firestore_repo import RealEstateRepository
from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository


def get_database_repository():
    """
    Factory function to get the appropriate database repository
    based on the DATABASE_TYPE configuration.
    """
    if settings.DATABASE_TYPE.lower() == "mysql":
        return MySQLRealEstateRepository()
    else:
        # Default to Firestore for backward compatibility
        return RealEstateRepository()
