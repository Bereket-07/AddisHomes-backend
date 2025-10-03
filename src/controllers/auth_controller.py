# src/controllers/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.app.startup import get_user_use_cases
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.user_models import User, UserRole, UserCreate
from src.utils.auth_utils import create_access_token
from src.utils.config import settings
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class SignupRequest(BaseModel):
    phone_number: str
    password: str
    role: UserRole
    display_name: Optional[str] = None

@router.post("/signup")
async def signup(request: SignupRequest, user_cases: UserUseCases = Depends(get_user_use_cases)):
    existing_user = await user_cases.repo.get_user_by_phone_number(request.phone_number)
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    create_data = UserCreate(
        phone_number=request.phone_number,
        telegram_id=0,
        display_name=request.display_name,
        roles=[request.role],
        language="en",
        password=request.password
    )
    new_user = await user_cases.repo.create_user(create_data)
    return {"detail": "User created successfully", "user_id": new_user.uid}

class LoginRequest(BaseModel):
    phone_number: str
    password: str

@router.post("/login")
async def login(request: LoginRequest, user_cases: UserUseCases = Depends(get_user_use_cases)):
    user = await user_cases.authenticate_user(request.phone_number, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect phone number or password")
    access_token = create_access_token(data={"sub": user.uid})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), user_cases: UserUseCases = Depends(get_user_use_cases)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        uid: str = payload.get("sub")
        if uid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await user_cases.get_user_by_id(uid)
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Profile Management ---
class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    phone_number: Optional[str] = None

@router.put("/users/me", response_model=User)
async def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    user_cases: UserUseCases = Depends(get_user_use_cases)
):
    return await user_cases.update_profile(current_user.uid, req.display_name, req.phone_number)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/users/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_cases: UserUseCases = Depends(get_user_use_cases)
):
    await user_cases.change_password(current_user.uid, req.current_password, req.new_password)
    return {"detail": "Password changed"}