# src/controllers/admin_controller.py (extended)
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, List
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import Property, PropertyStatus, PropertyCreate
from src.domain.models.car_models import Car, CarCreate, CarFilter, CarStatus
from src.app.startup import get_property_use_cases
from src.controllers.auth_controller import get_current_user
from src.domain.models.user_models import User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependency to ensure only ADMIN can access
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# -------------------------
# Property Management CRUD
# -------------------------
@router.get("/properties", response_model=List[Property])
async def get_all_properties(
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Admin can view ALL properties (any status, any broker)."""
    return await prop_cases.get_all_properties()

@router.get("/properties/{property_id}", response_model=Property)
async def get_property_by_id(
    property_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Admin can fetch details of any property."""
    return await prop_cases.get_property_details(property_id)

@router.post("/properties", response_model=Property)
async def create_property_as_admin(
    property_data: PropertyCreate,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Admin can directly create a property without being a broker."""
    return await prop_cases.submit_property(property_data)

@router.put("/properties/{property_id}", response_model=Property)
async def update_property_as_admin(
    property_id: str,
    property_data: PropertyCreate,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Admin can update any property details."""
    return await prop_cases.update_property(property_id, property_data)

@router.delete("/properties/{property_id}")
async def delete_property_as_admin(
    property_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Admin can delete any property."""
    await prop_cases.delete_property(property_id)
    return {"detail": "Property deleted successfully"}

# -------------------------
# Approvals & Analytics
# -------------------------
@router.get("/pending", response_model=List[Property])
async def get_pending_properties(
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.get_pending_properties()

@router.post("/approve/{property_id}", response_model=Property)
async def approve_property(
    property_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.approve_property(property_id)

@router.post("/reject/{property_id}", response_model=Property)
async def reject_property(
    property_id: str,
    reason: str = Body(..., embed=True),
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.reject_property(property_id, reason)

@router.post("/mark-sold/{property_id}", response_model=Property)
async def mark_as_sold(
    property_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.mark_property_as_sold(property_id)

@router.get("/analytics", response_model=Dict[str, Dict[str, int]])
async def get_analytics(
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    # Return combined analytics including properties and cars
    return await prop_cases.get_analytics_summary()

# -------------------------
# Car Management
# -------------------------

@router.get("/cars", response_model=List[Car])
async def get_all_cars(
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    # Admin needs all cars including pending for moderation
    return await prop_cases.repo.list_all_cars()

@router.post("/cars/approve/{car_id}", response_model=Car)
async def approve_car(
    car_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    # update car status to approved
    return await prop_cases.repo.update_car_status(car_id, CarStatus.APPROVED)

@router.post("/cars/reject/{car_id}", response_model=Car)
async def reject_car(
    car_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.repo.update_car_status(car_id, CarStatus.REJECTED)

@router.post("/cars/mark-sold/{car_id}", response_model=Car)
async def mark_car_sold(
    car_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.repo.update_car_status(car_id, CarStatus.SOLD)

@router.post("/cars", response_model=Car)
async def create_car_as_admin(
    car_data: CarCreate,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.submit_car(car_data)

@router.delete("/cars/{car_id}")
async def delete_car_as_admin(
    car_id: str,
    current_admin: User = Depends(get_current_admin_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    await prop_cases.repo.delete_car(car_id)
    return {"detail": "Car deleted successfully"}

