from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .common_models import PropertyType, PropertyStatus, Location, CondoScheme, FurnishingStatus

class PropertyBase(BaseModel):
    property_type: PropertyType
    location: Location
    bedrooms: int = Field(..., gt=0)
    bathrooms: int = Field(..., gt=0)
    size_sqm: float = Field(..., gt=0)
    price_etb: float = Field(..., gt=0)
    description: str
    image_urls: List[str] = Field(..., min_length=3)
    
    # Optional fields based on your requirements
    furnishing_status: Optional[FurnishingStatus] = None
    condominium_scheme: Optional[CondoScheme] = None
    floor_level: Optional[int] = None
    debt_status: Optional[str] = None
    structure_type: Optional[str] = None
    plot_size_sqm: Optional[float] = None
    title_deed: bool = False
    kitchen_type: Optional[str] = None
    living_rooms: Optional[int] = None
    water_tank: bool = False
    parking_spaces: Optional[int] = 0

class PropertyCreate(PropertyBase):
    broker_id: str
    broker_name: str

class PropertyInDB(PropertyCreate):
    pid: str
    status: PropertyStatus = PropertyStatus.PENDING
    created_at: datetime
    updated_at: datetime
    rejection_reason: Optional[str] = None

class Property(PropertyInDB):
    class Config:
        from_attributes = True

class PropertyFilter(BaseModel):
    status: Optional[PropertyStatus] = None
    property_type: Optional[PropertyType] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    location_region: Optional[str] = None
    location_city: Optional[str] = None
    location_sub_city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_size_sqm: Optional[float] = None
    max_size_sqm: Optional[float] = None
    condominium_scheme: Optional[CondoScheme] = None
    furnishing_status: Optional[FurnishingStatus] = None
    min_floor_level: Optional[int] = None