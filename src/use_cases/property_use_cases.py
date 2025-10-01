# src/use_cases/property_use_cases.py

from typing import List, Optional
from src.infrastructure.repository.firestore_repo import RealEstateRepository
from src.domain.models.car_models import Car, CarCreate, CarFilter, CarStatus
from src.domain.models.property_models import Property, PropertyCreate, PropertyFilter, PropertyStatus
from src.utils.exceptions import InvalidOperationError # <<< IMPORT

class PropertyUseCases:
    def __init__(self, repo: RealEstateRepository):
        self.repo = repo

    async def submit_property(self, property_data: PropertyCreate) -> Property:
        """Broker submits a new property. It is saved as 'pending'."""
        return await self.repo.create_property(property_data)

    async def get_pending_properties(self) -> List[Property]:
        """Admin fetches all properties awaiting approval."""
        return await self.repo.get_properties_by_status(PropertyStatus.PENDING)

    async def approve_property(self, property_id: str) -> Property: # <<< No longer Optional
        """Admin approves a property."""
        # --- NEW: Business Logic Check ---
        prop_to_approve = await self.repo.get_property_by_id(property_id)
        if prop_to_approve.status != PropertyStatus.PENDING:
            raise InvalidOperationError(f"Cannot approve property. Current status is '{prop_to_approve.status.value}'.")
        
        update_data = {"status": PropertyStatus.APPROVED.value, "rejection_reason": None}
        return await self.repo.update_property(property_id, update_data)

    async def reject_property(self, property_id: str, reason: str) -> Property: # <<< No longer Optional
        """Admin rejects a property with a given reason."""
        # --- NEW: Business Logic Check ---
        prop_to_reject = await self.repo.get_property_by_id(property_id)
        if prop_to_reject.status != PropertyStatus.PENDING:
            raise InvalidOperationError(f"Cannot reject property. Current status is '{prop_to_reject.status.value}'.")
            
        update_data = {"status": PropertyStatus.REJECTED.value, "rejection_reason": reason}
        return await self.repo.update_property(property_id, update_data)

    async def find_properties(self, filters: PropertyFilter) -> List[Property]:
        """Buyer/Admin/Broker finds approved properties based on filters."""
        return await self.repo.query_properties(filters)
    async def mark_property_as_sold(self, property_id: str) -> Property:
        """Admin marks an approved property as sold."""
        prop_to_sell = await self.repo.get_property_by_id(property_id)
        if prop_to_sell.status != PropertyStatus.APPROVED:
            raise InvalidOperationError(f"Cannot mark as sold. Property must be in 'approved' status.")
        
        update_data = {"status": PropertyStatus.SOLD.value}
        return await self.repo.update_property(property_id, update_data)
    async def delete_property(self, property_id: str):
        """Admin permanently deletes a property."""
        # Business logic checks could be added here if needed
        # For now, we allow deleting a property in any state
        await self.repo.delete_property(property_id)
        
    async def get_properties_by_broker(self, broker_id: str) -> List[Property]:
        """Broker fetches their own submitted properties."""
        return await self.repo.get_properties_by_broker_id(broker_id)

    async def get_property_details(self, property_id: str) -> Property: # <<< No longer Optional
        """Fetches full details for a single property."""
        return await self.repo.get_property_by_id(property_id)
    async def get_analytics_summary(self) -> dict:
        """Retrieves a summary of property and car counts by status."""
        prop_counts = await self.repo.count_properties_by_status()
        car_counts = await self.repo.count_cars_by_status()
        # serialize enums to string keys
        return {
            "properties": {status.value: count for status, count in prop_counts.items()},
            "cars": {status.value: count for status, count in car_counts.items()},
        }
    async def get_all_properties(self) -> List[Property]:
        """Admin fetches all properties, regardless of status or broker."""
        # Using an empty filter to get everything
        return await self.repo.query_properties(PropertyFilter())

    # --- Car Use-Cases ---
    async def submit_car(self, car_data: CarCreate) -> Car:
        # cars start as pending for admin approval
        if not getattr(car_data, 'status', None):
            car_data.status = CarStatus.PENDING
        return await self.repo.create_car(car_data)

    async def find_cars(self, filters: CarFilter) -> list[Car]:
        return await self.repo.query_cars(filters)

    async def get_car_details(self, car_id: str) -> Car:
        return await self.repo.get_car_by_id(car_id)

    async def get_cars_by_broker(self, broker_id: str) -> list[Car]:
        return await self.repo.get_cars_by_broker_id(broker_id)
