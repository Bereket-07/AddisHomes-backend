import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from google.cloud import firestore
from src.domain.models.user_models import User, UserCreate, UserInDB, UserRole
from src.domain.models.property_models import Property, PropertyCreate, PropertyInDB, PropertyFilter, PropertyStatus
from src.utils.config import settings

class RealEstateRepository:
    def __init__(self):
        self.db = firestore.AsyncClient()
        self.users_collection = self.db.collection('users')
        self.properties_collection = self.db.collection('properties')

    # --- User Methods ---
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        docs = self.users_collection.where('telegram_id', '==', telegram_id).limit(1).stream()
        async for doc in docs:
            user_data = doc.to_dict()
            return User(**user_data)
        return None

    async def get_user_by_id(self, uid: str) -> Optional[User]:
        doc = await self.users_collection.document(uid).get()
        if doc.exists:
            return User(**doc.to_dict())
        return None
        
    async def get_user_by_phone_number(self, phone_number: str) -> Optional[User]:
        """Finds a user by their phone number."""
        docs = self.users_collection.where('phone_number', '==', phone_number).limit(1).stream()
        async for doc in docs:
            return User(**doc.to_dict())
        return None

    async def create_user(self, user_data: UserCreate) -> User:
        uid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        user_in_db = UserInDB(
            uid=uid,
            created_at=now,
            updated_at=now,
            **user_data.model_dump()
        )
        await self.users_collection.document(uid).set(user_in_db.model_dump())
        return User(**user_in_db.model_dump())

    async def update_user(self, uid: str, updates: Dict[str, Any]) -> Optional[User]:
        doc_ref = self.users_collection.document(uid)
        if not (await doc_ref.get()).exists:
            return None
        
        updates['updated_at'] = datetime.now(timezone.utc)
        await doc_ref.update(updates)
        updated_doc = await doc_ref.get()
        return User(**updated_doc.to_dict())

    async def find_admin_user(self) -> Optional[User]:
        """Finds the user with the ADMIN role."""
        docs = self.users_collection.where('roles', 'array_contains', UserRole.ADMIN.value).limit(1).stream()
        async for doc in docs:
            return User(**doc.to_dict())
        return None

    async def find_unclaimed_admin(self) -> Optional[User]:
        """Finds an admin account that has not been linked to a Telegram ID yet."""
        query = self.users_collection.where('roles', 'array_contains', UserRole.ADMIN.value).where('telegram_id', '==', 0)
        docs = query.limit(1).stream()
        async for doc in docs:
            return User(**doc.to_dict())
        return None

    # --- Property Methods ---
    async def create_property(self, property_data: PropertyCreate) -> Property:
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        prop_in_db = PropertyInDB(
            pid=pid,
            created_at=now,
            updated_at=now,
            **property_data.model_dump()
        )
        await self.properties_collection.document(pid).set(prop_in_db.model_dump())
        return Property(**prop_in_db.model_dump())

    async def get_property_by_id(self, pid: str) -> Optional[Property]:
        doc = await self.properties_collection.document(pid).get()
        if doc.exists:
            return Property(**doc.to_dict())
        return None

    async def update_property(self, pid: str, updates: Dict[str, Any]) -> Optional[Property]:
        doc_ref = self.properties_collection.document(pid)
        if not (await doc_ref.get()).exists:
            return None
        
        updates['updated_at'] = datetime.now(timezone.utc)
        await doc_ref.update(updates)
        updated_doc = await doc_ref.get()
        return Property(**updated_doc.to_dict())

    async def get_properties_by_status(self, status: PropertyStatus) -> List[Property]:
        docs = self.properties_collection.where('status', '==', status.value).stream()
        return [Property(**doc.to_dict()) async for doc in docs]

    async def get_properties_by_broker_id(self, broker_id: str) -> List[Property]:
        docs = self.properties_collection.where('broker_id', '==', broker_id).stream()
        return [Property(**doc.to_dict()) async for doc in docs]

    async def query_properties(self, filters: PropertyFilter) -> List[Property]:
        query = self.properties_collection.where('status', '==', PropertyStatus.APPROVED.value)

        if filters.property_type:
            query = query.where('property_type', '==', filters.property_type.value)
        if filters.min_bedrooms:
            query = query.where('bedrooms', '>=', filters.min_bedrooms)
        if filters.max_bedrooms:
            query = query.where('bedrooms', '<=', filters.max_bedrooms)
        if filters.location_region:
            query = query.where('location.region', '==', filters.location_region)
        if filters.min_price:
            query = query.where('price_etb', '>=', filters.min_price)
        if filters.max_price:
            query = query.where('price_etb', '<=', filters.max_price)
        
        docs = query.stream()
        return [Property(**doc.to_dict()) async for doc in docs]