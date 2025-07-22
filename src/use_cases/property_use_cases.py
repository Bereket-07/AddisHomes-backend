from typing import List, Optional
from src.infrastructure.repository.firestore_repo import RealEstateRepository
from src.domain.models.property_models import Property, PropertyCreate, PropertyFilter, PropertyStatus

class PropertyUseCases:
    def __init__(self, repo: RealEstateRepository):
        self.repo = repo

    async def submit_property(self, property_data: PropertyCreate) -> Property:
        """Broker submits a new property. It is saved as 'pending'."""
        return await self.repo.create_property(property_data)

    async def get_pending_properties(self) -> List[Property]:
        """Admin fetches all properties awaiting approval."""
        return await self.repo.get_properties_by_status(PropertyStatus.PENDING)

    async def approve_property(self, property_id: str) -> Optional[Property]:
        """Admin approves a property."""
        update_data = {"status": PropertyStatus.APPROVED.value, "rejection_reason": None}
        return await self.repo.update_property(property_id, update_data)

    async def reject_property(self, property_id: str, reason: str) -> Optional[Property]:
        """Admin rejects a property with a given reason."""
        update_data = {"status": PropertyStatus.REJECTED.value, "rejection_reason": reason}
        return await self.repo.update_property(property_id, update_data)

    async def find_properties(self, filters: PropertyFilter) -> List[Property]:
        """Buyer/Admin/Broker finds approved properties based on filters."""
        return await self.repo.query_properties(filters)
        
    async def get_properties_by_broker(self, broker_id: str) -> List[Property]:
        """Broker fetches their own submitted properties."""
        return await self.repo.get_properties_by_broker_id(broker_id)

    async def get_property_details(self, property_id: str) -> Optional[Property]:
        """Fetches full details for a single property."""
        return await self.repo.get_property_by_id(property_id)