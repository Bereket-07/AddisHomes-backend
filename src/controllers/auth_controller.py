from flask import Blueprint, request, jsonify
from functools import wraps
from jose import jwt, JWTError
from src.app.startup import user_use_cases
from src.domain.models.user_models import UserCreate, UserRole
from src.utils.auth_utils import create_access_token
from src.utils.config import settings
from pydantic import BaseModel
from typing import Optional

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# -------------------------
# Decorators & Helpers
# -------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check Authorization header: "Bearer <token>"
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'detail': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            uid = payload.get("sub")
            if uid is None:
                 return jsonify({'detail': 'Invalid token payload'}), 401
            
            # Fetch user synchronously
            current_user = user_use_cases.get_user_by_id(uid)
            if not current_user:
                return jsonify({'detail': 'User not found'}), 401
                
        except JWTError:
            return jsonify({'detail': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'detail': f'Authentication error: {str(e)}'}), 500

        # Pass current_user to the wrapped function
        return f(current_user, *args, **kwargs)
    
    return decorated

# -------------------------
# Schemas
# -------------------------
class SignupRequest(BaseModel):
    phone_number: str
    password: str
    role: UserRole
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    phone_number: str
    password: str

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    phone_number: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# -------------------------
# Routes
# -------------------------
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
        req = SignupRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

    existing_user = user_use_cases.repo.get_user_by_phone_number(req.phone_number)
    if existing_user:
        return jsonify({"detail": "Phone number already registered"}), 400

    create_data = UserCreate(
        phone_number=req.phone_number,
        telegram_id=0,
        display_name=req.display_name,
        roles=[req.role],
        language="en",
        password=req.password
    )
    new_user = user_use_cases.repo.create_user(create_data)
    return jsonify({"detail": "User created successfully", "user_id": new_user.uid})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    # Handle form-data logic if needed, but JSON is standard here
    try:
        req = LoginRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

    user = user_use_cases.authenticate_user(req.phone_number, req.password)
    if not user:
        return jsonify({"detail": "Incorrect phone number or password"}), 401
        
    access_token = create_access_token(data={"sub": user.uid})
    return jsonify({"access_token": access_token, "token_type": "bearer"})

@auth_bp.route('/me', methods=['GET'])
@token_required
def read_users_me(current_user):
    return jsonify(current_user.dict())

@auth_bp.route('/users/me', methods=['PUT'])
@token_required
def update_profile_endpoint(current_user):
    data = request.get_json()
    try:
        req = UpdateProfileRequest(**data)
    except Exception as e:
         return jsonify({"detail": str(e)}), 400
         
    user = user_use_cases.update_profile(current_user.uid, req.display_name, req.phone_number)
    return jsonify(user.dict())

@auth_bp.route('/users/change-password', methods=['POST'])
@token_required
def change_password_endpoint(current_user):
    data = request.get_json()
    try:
        req = ChangePasswordRequest(**data)
    except Exception as e:
        return jsonify({"detail": str(e)}), 400
        
    try:
        user_use_cases.change_password(current_user.uid, req.current_password, req.new_password)
        return jsonify({"detail": "Password changed"})
    except Exception as e:
        return jsonify({"detail": str(e)}), 400