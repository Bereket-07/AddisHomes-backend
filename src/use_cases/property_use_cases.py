from typing import List, Optional
# Note: Type hint references might be misleading if repo is now generic or different
# but we keep imports for models
from src.domain.models.car_models import Car, CarCreate, CarFilter, CarStatus
from src.domain.models.property_models import Property, PropertyCreate, PropertyFilter, PropertyStatus
from src.utils.exceptions import InvalidOperationError

class PropertyUseCases:
    def __init__(self, repo):
        # repo is duck-typed, expected to have sync sync methods now
        self.repo = repo

    def submit_property(self, property_data: PropertyCreate) -> Property:
        """Broker submits a new property. It is saved as 'pending'."""
        return self.repo.create_property(property_data)

    def get_pending_properties(self) -> List[Property]:
        """Admin fetches all properties awaiting approval."""
        return self.repo.get_properties_by_status(PropertyStatus.PENDING)

    def approve_property(self, property_id: str) -> Property:
        """Admin approves a property."""
        prop_to_approve = self.repo.get_property_by_id(property_id)
        if prop_to_approve.status != PropertyStatus.PENDING:
            raise InvalidOperationError(f"Cannot approve property. Current status is '{prop_to_approve.status.value}'.")
        
        update_data = {"status": PropertyStatus.APPROVED.value, "rejection_reason": None}
        return self.repo.update_property(property_id, update_data)

    def reject_property(self, property_id: str, reason: str) -> Property:
        """Admin rejects a property with a given reason."""
        prop_to_reject = self.repo.get_property_by_id(property_id)
        if prop_to_reject.status != PropertyStatus.PENDING:
            raise InvalidOperationError(f"Cannot reject property. Current status is '{prop_to_reject.status.value}'.")
            
        update_data = {"status": PropertyStatus.REJECTED.value, "rejection_reason": reason}
        return self.repo.update_property(property_id, update_data)

    def find_properties(self, filters: PropertyFilter) -> List[Property]:
        """Buyer/Admin/Broker finds approved properties based on filters."""
        return self.repo.query_properties(filters)

    def mark_property_as_sold(self, property_id: str) -> Property:
        """Admin marks an approved property as sold."""
        prop_to_sell = self.repo.get_property_by_id(property_id)
        if prop_to_sell.status != PropertyStatus.APPROVED:
            raise InvalidOperationError(f"Cannot mark as sold. Property must be in 'approved' status.")
        
        update_data = {"status": PropertyStatus.SOLD.value}
        return self.repo.update_property(property_id, update_data)

    def delete_property(self, property_id: str):
        """Admin permanently deletes a property."""
        self.repo.delete_property(property_id)
        
    def get_properties_by_broker(self, broker_id: str) -> List[Property]:
        """Broker fetches their own submitted properties."""
        return self.repo.get_properties_by_broker_id(broker_id)

    def get_property_details(self, property_id: str) -> Property:
        """Fetches full details for a single property."""
        return self.repo.get_property_by_id(property_id)

    def update_property(self, property_id: str, updates: dict) -> Property:
        return self.repo.update_property(property_id, updates)

    def get_analytics_summary(self) -> dict:
        """Retrieves a summary of property and car counts by status."""
        prop_counts = self.repo.count_properties_by_status()
        car_counts = self.repo.count_cars_by_status()
        return {
            "properties": {status.value: count for status, count in prop_counts.items()},
            "cars": {status.value: count for status, count in car_counts.items()},
        }

    def get_all_properties(self) -> List[Property]:
        """Admin fetches all properties, regardless of status or broker."""
        return self.repo.query_properties(PropertyFilter())

    # --- Car Use-Cases ---
    def submit_car(self, car_data: CarCreate) -> Car:
        # cars start as pending for admin approval
        if not getattr(car_data, 'status', None):
            car_data.status = CarStatus.PENDING
        return self.repo.create_car(car_data)

    def find_cars(self, filters: CarFilter) -> list[Car]:
        return self.repo.query_cars(filters)

    def get_car_details(self, car_id: str) -> Car:
        return self.repo.get_car_by_id(car_id)

    def get_cars_by_broker(self, broker_id: str) -> list[Car]:
        return self.repo.get_cars_by_broker_id(broker_id)
