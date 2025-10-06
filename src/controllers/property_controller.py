# src/controllers/property_controller.py (updated)
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import Property, PropertyFilter, PropertyType, CondoScheme, PropertyCreate
from src.domain.models.car_models import Car, CarCreate, CarFilter, CarType
from src.app.startup import get_property_use_cases
from src.controllers.auth_controller import get_current_user
from src.domain.models.user_models import User, UserRole
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.get("/", response_model=List[Property])
async def find_properties_endpoint(
    property_type: PropertyType | None = Query(None),
    min_bedrooms: int | None = Query(None, gt=0),
    max_bedrooms: int | None = Query(None, gt=0),
    min_price: float | None = Query(None, gt=0),
    max_price: float | None = Query(None, gt=0),
    min_size_sqm: float | None = Query(None, gt=0),
    max_size_sqm: float | None = Query(None, gt=0),
    condominium_scheme: CondoScheme | None = Query(None),
    location_region: str | None = Query(None),
    location_site: str | None = Query(None),
    min_floor_level: int | None = Query(None, ge=0),
    furnishing_status: str | None = Query(None),
    filter_is_commercial: bool | None = Query(None),
    filter_has_elevator: bool | None = Query(None),
    filter_has_private_rooftop: bool | None = Query(None),
    filter_is_two_story_penthouse: bool | None = Query(None),
    filter_has_private_entrance: bool | None = Query(None),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    filters = PropertyFilter(
        property_type=property_type,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_price=min_price,
        max_price=max_price,
        min_size_sqm=min_size_sqm,
        max_size_sqm=max_size_sqm,
        condominium_scheme=condominium_scheme,
        location_region=location_region,
        location_site=location_site,
        min_floor_level=min_floor_level,
        furnishing_status=furnishing_status,
        filter_is_commercial=filter_is_commercial,
        filter_has_elevator=filter_has_elevator,
        filter_has_private_rooftop=filter_has_private_rooftop,
        filter_is_two_story_penthouse=filter_is_two_story_penthouse,
        filter_has_private_entrance=filter_has_private_entrance
    )
    properties = await prop_cases.find_properties(filters)
    return properties

@router.get("/me", response_model=List[Property])
async def get_my_properties(
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    if UserRole.BROKER not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only brokers can view their listings")
    return await prop_cases.get_properties_by_broker(current_user.uid)

@router.post("/", response_model=Property)
async def submit_property_endpoint(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    print("Received data:", property_data.dict())
    if UserRole.BROKER not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only brokers can submit properties")
    property_data.broker_id = current_user.uid
    property_data.broker_name = current_user.display_name or current_user.phone_number
    property_data.broker_phone = current_user.phone_number  # 👈 ensure phone is stored
    return await prop_cases.submit_property(property_data)

@router.get("/{property_id}", response_model=Property)
async def get_property_by_id_endpoint(
    property_id: str,
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    prop = await prop_cases.get_property_details(property_id)
    return prop

@router.post("/upload-images")
async def upload_images(
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Upload property images to DB and return served URLs (/images/{id})."""
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")

    # Ensure repo supports blob saving
    repo = getattr(prop_cases, 'repo', None)
    if not repo or not hasattr(repo, 'save_image_blob'):
        raise HTTPException(status_code=500, detail="Image storage not available")

    uploaded_urls: List[str] = []

    for image in images:
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"File {image.filename} is not an image")

        content = await image.read()
        image_id = uuid.uuid4().hex
        content_type = image.content_type
        try:
            await repo.save_image_blob(image_id=image_id, content_type=content_type, data=content)
            uploaded_urls.append(f"/images/{image_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store image {image.filename}: {str(e)}")

    return {"urls": uploaded_urls}

@router.post("/convert-telegram-images")
async def convert_telegram_images(
    image_urls: List[str],
    current_user: User = Depends(get_current_user)
):
    """Convert Telegram file IDs to proper image URLs"""
    # For now, return the file IDs as-is with a note
    # In production, you would implement actual Telegram file URL conversion
    converted_urls = []
    for url in image_urls:
        if url.startswith("AgACAgQAAxkBAAI") or len(url) > 50:
            # This is a Telegram file ID - for now, return a placeholder
            converted_urls.append(f"https://via.placeholder.com/400x300?text=Telegram+Image")
        else:
            # This is already a proper URL
            converted_urls.append(url)
    
    return {"converted_urls": converted_urls}


# ===== Car Endpoints =====
car_router = APIRouter(prefix="/cars", tags=["Cars"])

@car_router.get("/", response_model=List[Car])
async def find_cars_endpoint(
    car_type: CarType | None = Query(None),
    min_price: float | None = Query(None, gt=0),
    max_price: float | None = Query(None, gt=0),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    filters = CarFilter(
        car_type=car_type,
        min_price=min_price,
        max_price=max_price,
    )
    return await prop_cases.find_cars(filters)

@car_router.get("/me", response_model=List[Car])
async def get_my_cars(
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    if UserRole.BROKER not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only brokers can view their car listings")
    return await prop_cases.get_cars_by_broker(current_user.uid)

@car_router.post("/", response_model=Car)
async def submit_car_endpoint(
    car_data: CarCreate,
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    if UserRole.BROKER not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only brokers can submit cars")
    car_data.broker_id = current_user.uid
    car_data.broker_name = current_user.display_name or current_user.phone_number
    car_data.broker_phone = current_user.phone_number
    return await prop_cases.submit_car(car_data)

@car_router.get("/{car_id}", response_model=Car)
async def get_car_by_id_endpoint(
    car_id: str,
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    return await prop_cases.get_car_details(car_id)

@car_router.post("/upload-images")
async def upload_car_images(
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    prop_cases: PropertyUseCases = Depends(get_property_use_cases)
):
    """Upload car images to DB and return served URLs (/images/{id})."""
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")

    repo = getattr(prop_cases, 'repo', None)
    if not repo or not hasattr(repo, 'save_image_blob'):
        raise HTTPException(status_code=500, detail="Image storage not available")

    uploaded_urls: List[str] = []

    for image in images:
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"File {image.filename} is not an image")

        content = await image.read()
        image_id = uuid.uuid4().hex
        content_type = image.content_type
        try:
            await repo.save_image_blob(image_id=image_id, content_type=content_type, data=content)
            uploaded_urls.append(f"/images/{image_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to store image {image.filename}: {str(e)}")

    return {"urls": uploaded_urls}