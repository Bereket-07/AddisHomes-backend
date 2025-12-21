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


# --- Dependency Injection ---
# In Flask, we can just import `user_use_cases` and `property_use_cases` directly
# or use `current_app` context, but simple imports work for this scale.