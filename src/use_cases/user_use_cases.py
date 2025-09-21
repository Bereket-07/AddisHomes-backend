from typing import Optional
from src.infrastructure.repository.firestore_repo import RealEstateRepository
from src.domain.models.user_models import User, UserCreate, UserRole
from src.utils.config import settings
from src.utils.exceptions import UserNotFoundError
from src.utils.i18n import translations
from src.utils.auth_utils import hash_password ,verify_password, create_access_token


class UserUseCases:
    def __init__(self, repo: RealEstateRepository):
        self.repo = repo

    async def initialize_admin_user(self):
        """
        Checks if an admin user exists, and creates a placeholder if not.
        This is called on application startup.
        """
        admin_user = await self.repo.get_user_by_phone_number(settings.ADMIN_PHONE_NUMBER)
        if not admin_user:
            admin_data = UserCreate(
                phone_number=settings.ADMIN_PHONE_NUMBER,
                telegram_id=0,  # Placeholder ID for an unclaimed account
                display_name="Admin",
                roles=[UserRole.ADMIN]
            )
            await self.repo.create_user(admin_data)
            print(f"Placeholder admin account created for {settings.ADMIN_PHONE_NUMBER}.")

    async def get_or_create_user_by_telegram_id(self, telegram_id: int, display_name: Optional[str]) -> User:
        """
        Gets a user by their Telegram ID.
        If not found, it checks if this user is the one to claim the admin account.
        Otherwise, it creates a new regular user.
        """
        # 1. Check if user already exists with this telegram_id
        existing_user = await self.repo.get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user

        # 2. If not, check if this is the admin logging in for the first time
        unclaimed_admin = await self.repo.find_unclaimed_admin()
        if unclaimed_admin:
            # This is the admin! Claim the account by updating the telegram_id.
            updates = {"telegram_id": telegram_id, "display_name": display_name}
            claimed_admin_user = await self.repo.update_user(unclaimed_admin.uid, updates)
            print(f"Admin account for {claimed_admin_user.phone_number} claimed by Telegram user {telegram_id}.")
            return claimed_admin_user

        # 3. If it's not the admin, create a new regular user
        new_user_data = UserCreate(
            phone_number="N/A",
            telegram_id=telegram_id,
            display_name=display_name,
            roles=[]  # New users start with no roles, they select one
        )
        return await self.repo.create_user(new_user_data)
        
    async def get_user_by_id(self, uid: str) -> Optional[User]:
        return await self.repo.get_user_by_id(uid)

    async def get_admin_telegram_id(self) -> Optional[int]:
        """Finds the admin user and returns their Telegram ID."""
        admin_user = await self.repo.find_admin_user()
        if admin_user and admin_user.telegram_id != 0:
            return admin_user.telegram_id
        return None

    async def add_user_role(self, user_id: str, role: UserRole) -> User:
        """Adds a role to a user if they don't already have it."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(identifier=user_id) # <<< Be explicit on error
        
        if role not in user.roles:
            updated_roles = user.roles + [role]
            return await self.repo.update_user(user_id, {"roles": [r.value for r in updated_roles]})
        
        return user
    async def set_user_language(self, user_id: str, lang_code: str) -> User:
        """Sets the user's preferred language."""
        if lang_code not in translations:
            lang_code = 'en' # Default to english if invalid code is passed
        return await self.repo.update_user(user_id, {"language": lang_code})
    async def authenticate_user(self, phone_number: str, password: str) -> Optional[User]:
        user = await self.repo.get_user_by_phone_number(phone_number)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user