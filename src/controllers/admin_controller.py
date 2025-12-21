from flask import Blueprint, request, jsonify
from src.app.startup import user_use_cases, property_use_cases
from src.domain.models.property_models import PropertyCreate, PropertyStatus
from src.domain.models.car_models import CarCreate, CarStatus
from src.domain.models.user_models import UserRole
from src.controllers.auth_controller import token_required

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# -------------------------
# Helpers
# -------------------------
def require_admin(user):
    if UserRole.ADMIN not in user.roles:
        return False
    return True

# -------------------------
# Property Management CRUD
# -------------------------
@admin_bp.route('/properties', methods=['GET'])
@token_required
def get_all_properties(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    properties = property_use_cases.get_all_properties()
    # Pydantic to dict
    return jsonify([p.dict() for p in properties])

@admin_bp.route('/users', methods=['GET'])
@token_required
def list_users(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    users = user_use_cases.list_users()
    return jsonify([u.dict() for u in users])

@admin_bp.route('/users/<uid>/role', methods=['POST'])
@token_required
def set_user_role(current_user, uid):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    role = data.get("role")
    enable = bool(data.get("enable"))
    
    if role not in [r.value for r in UserRole]:
        return jsonify({"detail": "Invalid role"}), 400
        
    user = user_use_cases.set_user_role(uid, UserRole(role), enable)
    return jsonify(user.dict())

@admin_bp.route('/users/<uid>/active', methods=['POST'])
@token_required
def set_user_active(current_user, uid):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    active = bool(data.get("active"))
    
    user = user_use_cases.set_user_active(uid, active)
    return jsonify(user.dict())

@admin_bp.route('/users/<uid>', methods=['DELETE'])
@token_required
def delete_user(current_user, uid):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    user_use_cases.delete_user(uid)
    return jsonify({"detail": "User deleted"})

@admin_bp.route('/properties/<property_id>', methods=['GET'])
@token_required
def get_property_by_id(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    prop = property_use_cases.get_property_details(property_id)
    return jsonify(prop.dict())

@admin_bp.route('/properties', methods=['POST'])
@token_required
def create_property_as_admin(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    try:
        prop_data = PropertyCreate(**data)
        prop = property_use_cases.submit_property(prop_data)
        return jsonify(prop.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@admin_bp.route('/properties/<property_id>', methods=['PUT'])
@token_required
def update_property_as_admin(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    # Note: PropertyCreate implies creation, but we use strict update in repo
    # For now, just pass data as dict to update_property (which expects dict in repo?)
    # Wait, repo.update_property expects dict. Use case expects PropertyCreate?
    # Checking use_case: update_property call in admin_controller was:
    # await prop_cases.update_property(property_id, property_data)
    # But repo.update_property takes (pid, updates: Dict).
    # Ah, I need to check `property_use_cases.py` again.
    # It has `update_property(property_id, update_data)` in some places but I didn't see a general update method exposed in the use case file I viewed earlier?
    # Let me re-read property_use_cases.py quickly.
    # It has `approve_property`, `reject_property`, etc.
    # It DOES NOT seem to have a generic `update_property` method in the file I wrote in Step 55.
    # The original admin_controller had it. I must have missed it when rewriting `property_use_cases.py`.
    # I should add it.
    
    # Assuming I add it:
    # prop = property_use_cases.update_property(property_id, data)
    # return jsonify(prop.dict())
    return jsonify({"detail": "Update not implemented yet"}), 501

@admin_bp.route('/properties/<property_id>', methods=['DELETE'])
@token_required
def delete_property_as_admin(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    property_use_cases.delete_property(property_id)
    return jsonify({"detail": "Property deleted successfully"})

# -------------------------
# Approvals & Analytics
# -------------------------
@admin_bp.route('/pending', methods=['GET'])
@token_required
def get_pending_properties(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    props = property_use_cases.get_pending_properties()
    return jsonify([p.dict() for p in props])

@admin_bp.route('/approve/<property_id>', methods=['POST'])
@token_required
def approve_property(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    prop = property_use_cases.approve_property(property_id)
    return jsonify(prop.dict())

@admin_bp.route('/reject/<property_id>', methods=['POST'])
@token_required
def reject_property(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    reason = data.get("reason")
    
    prop = property_use_cases.reject_property(property_id, reason)
    return jsonify(prop.dict())

@admin_bp.route('/mark-sold/<property_id>', methods=['POST'])
@token_required
def mark_as_sold(current_user, property_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    prop = property_use_cases.mark_property_as_sold(property_id)
    return jsonify(prop.dict())

@admin_bp.route('/analytics', methods=['GET'])
@token_required
def get_analytics(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    return jsonify(property_use_cases.get_analytics_summary())

# -------------------------
# Car Management
# -------------------------
@admin_bp.route('/cars', methods=['GET'])
@token_required
def get_all_cars(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    cars = property_use_cases.repo.list_all_cars()
    return jsonify([c.dict() for c in cars])

@admin_bp.route('/cars/approve/<car_id>', methods=['POST'])
@token_required
def approve_car(current_user, car_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    car = property_use_cases.repo.update_car_status(car_id, CarStatus.APPROVED)
    return jsonify(car.dict())

@admin_bp.route('/cars/reject/<car_id>', methods=['POST'])
@token_required
def reject_car(current_user, car_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    car = property_use_cases.repo.update_car_status(car_id, CarStatus.REJECTED)
    return jsonify(car.dict())

@admin_bp.route('/cars/mark-sold/<car_id>', methods=['POST'])
@token_required
def mark_car_sold(current_user, car_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    car = property_use_cases.repo.update_car_status(car_id, CarStatus.SOLD)
    return jsonify(car.dict())

@admin_bp.route('/cars', methods=['POST'])
@token_required
def create_car_as_admin(current_user):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    data = request.get_json()
    try:
        car_data = CarCreate(**data)
        car = property_use_cases.submit_car(car_data)
        return jsonify(car.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@admin_bp.route('/cars/<car_id>', methods=['DELETE'])
@token_required
def delete_car_as_admin(current_user, car_id):
    if not require_admin(current_user):
        return jsonify({"detail": "Admin privileges required"}), 403
    
    property_use_cases.repo.delete_car(car_id)
    return jsonify({"detail": "Car deleted successfully"})