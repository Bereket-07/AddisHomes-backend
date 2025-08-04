from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class UserRole(str, Enum):
    BUYER = "buyer"
    BROKER = "broker"
    ADMIN = "admin"

class PropertyType(str, Enum):
    APARTMENT = "Apartment"
    CONDOMINIUM = "Condominium"
    VILLA = "Villa"
    BUILDING = "Building"          # <<< NEW
    PENTHOUSE = "Penthouse"        # <<< NEW
    DUPLEX = "Duplex"              # <<< NEW

class PropertyStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SOLD = "sold"

class Location(BaseModel):
    region: str
    city: str
    sub_city: Optional[str] = None
    specific_area: Optional[str] = None

class CondoScheme(str, Enum):
    S20_80 = "20/80"
    S40_60 = "40/60"
    S10_90 = "10/90"

class FurnishingStatus(str, Enum):
    UNFURNISHED = "Unfurnished"
    SEMI_FURNISHED = "Semi-furnished"
    FULLY_FURNISHED = "Fully-furnished"