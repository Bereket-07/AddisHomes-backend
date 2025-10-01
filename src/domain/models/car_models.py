from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CarType(str, Enum):
    SEDAN = "Sedan"
    AUTOMOBILE = "Automobile"
    VAN_MINIVAN = "Van/Minivan"
    PICKUP = "Pickup Truck"
    ELECTRIC_HYBRID = "Electric/Hybrid"
    LUXURY_PREMIUM = "Luxury/Premium"


class CarStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SOLD = "sold"


class CarBase(BaseModel):
    car_type: CarType
    price_etb: float = Field(..., gt=0)
    images: List[str] = Field(default_factory=list)
    status: CarStatus = CarStatus.PENDING

    # Basics
    manufacturer: Optional[str] = None  # e.g., Toyota
    model_name: Optional[str] = None    # e.g., Corolla
    model_year: Optional[int] = None
    color: Optional[str] = None
    plate: Optional[str] = None

    # Specs
    engine: Optional[str] = None        # e.g., 1.8L, V6
    power_hp: Optional[int] = None
    transmission: Optional[str] = None  # Automatic/Manual/Other
    fuel_efficiency_kmpl: Optional[float] = None
    motor_type: Optional[str] = None    # Benzene/Diesel/Electric/Hybrid/etc
    mileage_km: Optional[float] = None  # driven distance for used cars

    # Meta
    description: Optional[str] = None


class CarCreate(CarBase):
    broker_id: Optional[str] = None
    broker_name: Optional[str] = None
    broker_phone: Optional[str] = None


class CarInDB(CarCreate):
    cid: str
    created_at: datetime
    updated_at: datetime


class Car(CarInDB):
    pass


class CarFilter(BaseModel):
    car_type: Optional[CarType] = None
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)




