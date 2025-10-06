# src/utils/auth_utils.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_bcrypt(password: str) -> str:
    """Bcrypt only considers first 72 bytes; safely truncate to avoid backend errors."""
    try:
        # encode to bytes, slice 72 bytes, then decode ignoring errors
        return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    except Exception:
        return password[:72]

def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_bcrypt(password))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_truncate_bcrypt(plain_password), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt