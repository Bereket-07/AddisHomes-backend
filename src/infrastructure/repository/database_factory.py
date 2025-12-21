"""
Database Factory for switching between Firestore and MySQL
"""
from src.utils.config import settings
from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository


def get_database_repository():
    """
    Factory function to get the appropriate database repository
    based on the DATABASE_TYPE configuration.
    """
    return MySQLRealEstateRepository()
