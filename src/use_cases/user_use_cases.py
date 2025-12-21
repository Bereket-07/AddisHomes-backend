from typing import Optional
from src.domain.models.user_models import User, UserCreate, UserRole
from src.utils.config import settings
from src.utils.exceptions import UserNotFoundError
from src.utils.i18n import translations
from src.utils.auth_utils import hash_password ,verify_password

class UserUseCases:
    def __init__(self, repo):
        # repo is duck-typed, expected to have sync sync methods now
        self.repo = repo

    def initialize_admin_user(self):
        """
        Checks if an admin user exists, and creates a placeholder if not.
        This is called on application startup.
        """
        admin_user = self.repo.get_user_by_phone_number(settings.ADMIN_PHONE_NUMBER)
        if not admin_user:
            admin_data = UserCreate(
                phone_number=settings.ADMIN_PHONE_NUMBER,
                telegram_id=0,  # Placeholder ID for an unclaimed account
                display_name="Admin",
                roles=[UserRole.ADMIN]
            )
            self.repo.create_user(admin_data)
            print(f"Placeholder admin account created for {settings.ADMIN_PHONE_NUMBER}.")

    def get_or_create_user_by_telegram_id(self, telegram_id: int, display_name: Optional[str]) -> User:
        """
        Gets a user by their Telegram ID.
        If not found, it checks if this user is the one to claim the admin account.
        Otherwise, it creates a new regular user.
        """
        # 1. Check if user already exists with this telegram_id
        existing_user = self.repo.get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user

        # 2. If not, check if this is the admin logging in for the first time
        unclaimed_admin = self.repo.find_unclaimed_admin()
        if unclaimed_admin:
            # This is the admin! Claim the account by updating the telegram_id.
            updates = {"telegram_id": telegram_id, "display_name": display_name}
            claimed_admin_user = self.repo.update_user(unclaimed_admin.uid, updates)
            print(f"Admin account for {claimed_admin_user.phone_number} claimed by Telegram user {telegram_id}.")
            return claimed_admin_user

        # 3. If it's not the admin, create a new regular user
        new_user_data = UserCreate(
            phone_number="N/A",
            telegram_id=telegram_id,
            display_name=display_name,
            roles=[]  # New users start with no roles, they select one
        )
        return self.repo.create_user(new_user_data)
        
    def get_user_by_id(self, uid: str) -> Optional[User]:
        return self.repo.get_user_by_id(uid)

    def get_admin_telegram_id(self) -> Optional[int]:
        """Finds the admin user and returns their Telegram ID."""
        admin_user = self.repo.find_admin_user()
        if admin_user and admin_user.telegram_id != 0:
            return admin_user.telegram_id
        return None

    def add_user_role(self, user_id: str, role: UserRole) -> User:
        """Adds a role to a user if they don't already have it."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(identifier=user_id)
        
        if role not in user.roles:
            updated_roles = user.roles + [role]
            return self.repo.update_user(user_id, {"roles": [r.value for r in updated_roles]})
        
        return user

    # --- Admin: Users Listing & Management ---
    def list_users(self) -> list[User]:
        return self.repo.list_users()

    def set_user_role(self, uid: str, role: UserRole, enable: bool) -> User:
        return self.repo.set_user_role(uid, role, enable)

    def set_user_active(self, uid: str, active: bool) -> User:
        return self.repo.set_user_active(uid, active)

    def delete_user(self, uid: str) -> None:
        return self.repo.delete_user(uid)

    # --- Profile Management ---
    def update_profile(self, uid: str, display_name: str | None, phone_number: str | None) -> User:
        updates = {}
        if display_name is not None:
            updates["display_name"] = display_name
        if phone_number is not None:
            updates["phone_number"] = phone_number
        if not updates:
            return self.repo.get_user_by_id(uid)
        return self.repo.update_user(uid, updates)

    def change_password(self, uid: str, current_password: str, new_password: str) -> None:
        user = self.repo.get_user_by_id(uid)
        if not user or not user.hashed_password:
            raise UserNotFoundError(identifier=uid)
        if not verify_password(current_password, user.hashed_password):
            raise UserNotFoundError(identifier="invalid_credentials")
        new_hash = hash_password(new_password)
        self.repo.update_user(uid, {"hashed_password": new_hash})

    def set_user_language(self, user_id: str, lang_code: str) -> User:
        """Sets the user's preferred language."""
        if lang_code not in translations:
            lang_code = 'en' # Default to english if invalid code is passed
        return self.repo.update_user(user_id, {"language": lang_code})

    def authenticate_user(self, phone_number: str, password: str) -> Optional[User]:
        user = self.repo.get_user_by_phone_number(phone_number)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user