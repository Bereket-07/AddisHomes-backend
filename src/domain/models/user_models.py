# src/domain/models/user_models.py (updated)
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .common_models import UserRole

class UserBase(BaseModel):
    phone_number: str = Field(..., description="Primary user identifier, e.g., +251911123456")
    telegram_id: int
    display_name: Optional[str] = None
    roles: List[UserRole] = Field(default_factory=list)
    language: str = Field(default="en", description="User's preferred language code (e.g., 'en', 'am')")

class UserCreate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    uid: str
    created_at: datetime
    updated_at: datetime
    hashed_password: Optional[str] = None

class User(UserInDB):
    class Config:
        from_attributes = True