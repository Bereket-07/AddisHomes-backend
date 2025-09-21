import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError
from src.domain.models.user_models import User, UserCreate, UserInDB, UserRole
from google.cloud.firestore_v1.base_query import FieldFilter
from src.domain.models.property_models import Property, PropertyCreate, PropertyInDB, PropertyFilter, PropertyStatus
from src.utils.config import settings
from src.utils.exceptions import DatabaseError, UserNotFoundError, PropertyNotFoundError
from src.utils.auth_utils import hash_password ,verify_password, create_access_token


class RealEstateRepository:
    def __init__(self):
        self.db = firestore.AsyncClient()
        self.users_collection = self.db.collection('users')
        self.properties_collection = self.db.collection('properties')

    # --- User Methods (Unchanged) ---
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        try:
            docs = self.users_collection.where('telegram_id', '==', telegram_id).limit(1).stream()
            async for doc in docs:
                user_data = doc.to_dict()
                return User(**user_data)
            return None
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting user by telegram_id: {e}")

    async def get_user_by_id(self, uid: str) -> User:
        try:
            doc = await self.users_collection.document(uid).get()
            if not doc.exists:
                raise UserNotFoundError(identifier=uid)
            return User(**doc.to_dict())
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting user by ID: {e}")
        
    async def get_user_by_phone_number(self, phone_number: str) -> Optional[User]:
        """Finds a user by their phone number."""
        try:
            docs = self.users_collection.where('phone_number', '==', phone_number).limit(1).stream()
            async for doc in docs:
                return User(**doc.to_dict())
            return None
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting user by phone: {e}")

    async def create_user(self, user_data: UserCreate) -> User:
            uid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            user_in_db_dict = {
                "uid": uid,
                "created_at": now,
                "updated_at": now,
                **user_data.model_dump(exclude={"password"})
            }
            if user_data.password:
                user_in_db_dict["hashed_password"] = hash_password(user_data.password)
            user_in_db = UserInDB(**user_in_db_dict)
            try:
                await self.users_collection.document(uid).set(user_in_db.model_dump())
                return User(**user_in_db.model_dump(exclude={"hashed_password"}))
            except GoogleAPICallError as e:
                raise DatabaseError(f"Firestore error while creating user: {e}")

    async def update_user(self, uid: str, updates: Dict[str, Any]) -> User:
        doc_ref = self.users_collection.document(uid)
        try:
            if not (await doc_ref.get()).exists:
                raise UserNotFoundError(identifier=uid)
            
            updates['updated_at'] = datetime.now(timezone.utc)
            await doc_ref.update(updates)
            updated_doc = await doc_ref.get()
            return User(**updated_doc.to_dict())
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while updating user: {e}")

    async def find_admin_user(self) -> Optional[User]:
        """Finds the user with the ADMIN role."""
        try:
            docs = self.users_collection.where('roles', 'array_contains', UserRole.ADMIN.value).limit(1).stream()
            async for doc in docs:
                return User(**doc.to_dict())
            return None
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while finding admin user: {e}")

    async def find_unclaimed_admin(self) -> Optional[User]:
        """Finds an admin account that has not been linked to a Telegram ID yet."""
        try:
            query = self.users_collection.where('roles', 'array_contains', UserRole.ADMIN.value).where('telegram_id', '==', 0)
            docs = query.limit(1).stream()
            async for doc in docs:
                return User(**doc.to_dict())
            return None
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while finding unclaimed admin: {e}")

    # --- Property Methods (Unchanged except query_properties) ---
    async def create_property(self, property_data: PropertyCreate) -> Property:
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        prop_in_db = PropertyInDB(
            pid=pid,
            created_at=now,
            updated_at=now,
            **property_data.model_dump()
        )
        try:
            await self.properties_collection.document(pid).set(prop_in_db.model_dump())
            return Property(**prop_in_db.model_dump())
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while creating property: {e}")

    async def get_property_by_id(self, pid: str) -> Property:
        try:
            doc = await self.properties_collection.document(pid).get()
            if not doc.exists:
                raise PropertyNotFoundError(identifier=pid)
            return Property(**doc.to_dict())
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting property by ID: {e}")

    async def update_property(self, pid: str, updates: Dict[str, Any]) -> Property:
        doc_ref = self.properties_collection.document(pid)
        try:
            if not (await doc_ref.get()).exists:
                raise PropertyNotFoundError(identifier=pid)
            
            updates['updated_at'] = datetime.now(timezone.utc)
            await doc_ref.update(updates)
            updated_doc = await doc_ref.get()
            return Property(**updated_doc.to_dict())
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while updating property: {e}")

    async def get_properties_by_status(self, status: PropertyStatus) -> List[Property]:
        try:
            docs = self.properties_collection.where('status', '==', status.value).stream()
            return [Property(**doc.to_dict()) async for doc in docs]
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting properties by status: {e}")

    async def get_properties_by_broker_id(self, broker_id: str) -> List[Property]:
        try:
            docs = self.properties_collection.where('broker_id', '==', broker_id).stream()
            return [Property(**doc.to_dict()) async for doc in docs]
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while getting properties by broker ID: {e}")

    async def query_properties(self, filters: PropertyFilter) -> List[Property]:
        # --- UPDATED ---
        try:
            status_to_query = filters.status.value if filters.status else PropertyStatus.APPROVED.value
            query = self.properties_collection.where(filter=FieldFilter('status', '==', status_to_query))

            if filters.property_type:
                query = query.where(filter=FieldFilter('property_type', '==', filters.property_type.value))
            if filters.min_bedrooms:
                query = query.where(filter=FieldFilter('bedrooms', '>=', filters.min_bedrooms))
            if filters.max_bedrooms:
                query = query.where(filter=FieldFilter('bedrooms', '<=', filters.max_bedrooms))
            if filters.location_region:
                query = query.where(filter=FieldFilter('location.region', '==', filters.location_region))
            
            # --- UPDATED: Filter by site instead of sub_city ---
            if filters.location_site:
                query = query.where(filter=FieldFilter('location.site', '==', filters.location_site))
            
            if filters.min_price:
                query = query.where(filter=FieldFilter('price_etb', '>=', filters.min_price))
            if filters.max_price:
                query = query.where(filter=FieldFilter('price_etb', '<=', filters.max_price))
            if filters.filter_is_commercial is not None:
                query = query.where('is_commercial', '==', filters.filter_is_commercial)
            if filters.filter_has_elevator is not None:
                query = query.where('has_elevator', '==', filters.filter_has_elevator)
            if filters.filter_has_private_rooftop is not None:
                query = query.where('has_private_rooftop', '==', filters.filter_has_private_rooftop)
            if filters.filter_is_two_story_penthouse is not None:
                query = query.where('is_two_story_penthouse', '==', filters.filter_is_two_story_penthouse)
            if filters.filter_has_private_entrance is not None:
                query = query.where('has_private_entrance', '==', filters.filter_has_private_entrance)
            if filters.min_floor_level is not None:
                pass # Post-query filtering
            
            docs_stream = query.stream()
            all_results = [Property(**doc.to_dict()) async for doc in docs_stream]

            # --- POST-QUERY FILTERING IN PYTHON (Unchanged) ---
            if filters.min_floor_level is not None:
                final_results = [
                    prop for prop in all_results 
                    if prop.floor_level is not None and prop.floor_level >= filters.min_floor_level
                ]
                return final_results

            return all_results
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while querying properties: {e}")
            
    async def delete_property(self, pid: str) -> None:
        """Permanently deletes a property document from Firestore."""
        doc_ref = self.properties_collection.document(pid)
        try:
            if not (await doc_ref.get()).exists:
                raise PropertyNotFoundError(identifier=pid)
            
            await doc_ref.delete()
            return
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while deleting property: {e}")

    async def count_properties_by_status(self) -> dict[PropertyStatus, int]:
        """Counts all properties grouped by their status using efficient aggregation."""
        counts = {status: 0 for status in PropertyStatus}
        try:
            for status in PropertyStatus:
                query = self.properties_collection.where('status', '==', status.value)
                count_query = query.count()
                query_result = await count_query.get()
                counts[status] = query_result[0][0].value
            return counts
        except GoogleAPICallError as e:
            raise DatabaseError(f"Firestore error while counting properties: {e}")