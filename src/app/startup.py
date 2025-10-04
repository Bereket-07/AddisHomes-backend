import logging
from src.infrastructure.repository.database_factory import get_database_repository
from src.use_cases.user_use_cases import UserUseCases
from src.use_cases.property_use_cases import PropertyUseCases
from src.utils.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- Singleton Instances ---
# These are instantiated once and shared across the application,
# ensuring a single point of access to our services.

# Repository Layer
repo = get_database_repository()

# Use Case Layer
user_use_cases = UserUseCases(repo=repo)
property_use_cases = PropertyUseCases(repo=repo)


# --- Dependency Injection Functions for FastAPI ---
# These functions are used by FastAPI's `Depends` to provide
# the singleton instances to the API endpoints.

def get_user_use_cases() -> UserUseCases:
    return user_use_cases

def get_property_use_cases() -> PropertyUseCases:
    return property_use_cases