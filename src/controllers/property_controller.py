from flask import Blueprint, request, jsonify
from src.app.startup import property_use_cases
from src.domain.models.property_models import PropertyCreate, PropertyFilter, PropertyType, CondoScheme
from src.domain.models.car_models import CarCreate, CarFilter, CarType
from src.domain.models.user_models import UserRole
from src.controllers.auth_controller import token_required
import uuid

# Define Blueprints
property_bp = Blueprint('properties', __name__, url_prefix='/properties')
car_bp = Blueprint('cars', __name__, url_prefix='/cars')

# -------------------------
# Property Endpoints
# -------------------------
@property_bp.route('/', methods=['GET'])
def find_properties_endpoint():
    # Extract query params
    args = request.args
    
    # Helper to convert "true"/"false" strings to bool
    def get_bool(key):
        val = args.get(key)
        if val is None: return None
        return val.lower() == 'true'

    # Helper for int/float
    def get_val(key, type_func):
        val = args.get(key)
        if val is None: return None
        try: return type_func(val)
        except: return None
    
    # Enum handling: simple string pass-through, pydantic validates later or we map here
    # PropertyFilter likely expects Enums or compatible strings if configured
    
    try:
        property_type_val = args.get('property_type')
        condo_scheme_val = args.get('condominium_scheme')
        
        filters = PropertyFilter(
            property_type=PropertyType(property_type_val) if property_type_val else None,
            min_bedrooms=get_val('min_bedrooms', int),
            max_bedrooms=get_val('max_bedrooms', int),
            min_price=get_val('min_price', float),
            max_price=get_val('max_price', float),
            min_size_sqm=get_val('min_size_sqm', float),
            max_size_sqm=get_val('max_size_sqm', float),
            condominium_scheme=CondoScheme(condo_scheme_val) if condo_scheme_val else None,
            location_region=args.get('location_region'),
            location_site=args.get('location_site'),
            min_floor_level=get_val('min_floor_level', int),
            furnishing_status=args.get('furnishing_status'),
            filter_is_commercial=get_bool('filter_is_commercial'),
            filter_has_elevator=get_bool('filter_has_elevator'),
            filter_has_private_rooftop=get_bool('filter_has_private_rooftop'),
            filter_is_two_story_penthouse=get_bool('filter_is_two_story_penthouse'),
            filter_has_private_entrance=get_bool('filter_has_private_entrance')
        )
        properties = property_use_cases.find_properties(filters)
        return jsonify([p.dict() for p in properties])
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@property_bp.route('/me', methods=['GET'])
@token_required
def get_my_properties(current_user):
    if UserRole.BROKER not in current_user.roles:
        return jsonify({"detail": "Only brokers can view their listings"}), 403
    
    props = property_use_cases.get_properties_by_broker(current_user.uid)
    return jsonify([p.dict() for p in props])

@property_bp.route('/', methods=['POST'])
@token_required
def submit_property_endpoint(current_user):
    if UserRole.BROKER not in current_user.roles:
        return jsonify({"detail": "Only brokers can submit properties"}), 403
    
    data = request.get_json()
    print("Received data:", data)
    
    try:
        property_data = PropertyCreate(**data)
        property_data.broker_id = current_user.uid
        property_data.broker_name = current_user.display_name or current_user.phone_number
        property_data.broker_phone = current_user.phone_number
        
        prop = property_use_cases.submit_property(property_data)
        return jsonify(prop.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@property_bp.route('/<property_id>', methods=['GET'])
def get_property_by_id_endpoint(property_id):
    try:
        prop = property_use_cases.get_property_details(property_id)
        return jsonify(prop.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 404

@property_bp.route('/upload-images', methods=['POST'])
@token_required
def upload_images(current_user):
    if 'images' not in request.files:
        return jsonify({"detail": "No images provided"}), 400
    
    files = request.files.getlist('images')
    if not files:
        return jsonify({"detail": "No images provided"}), 400

    repo = getattr(property_use_cases, 'repo', None)
    if not repo or not hasattr(repo, 'save_image_blob'):
         return jsonify({"detail": "Image storage not available"}), 500

    uploaded_urls = []
    
    for image in files:
        if not image.content_type or not image.content_type.startswith('image/'):
             return jsonify({"detail": f"File {image.filename} is not an image"}), 400
        
        content = image.read()
        image_id = uuid.uuid4().hex
        content_type = image.content_type
        
        try:
            repo.save_image_blob(image_id=image_id, content_type=content_type, data=content)
            uploaded_urls.append(f"/images/{image_id}")
        except Exception as e:
            return jsonify({"detail": f"Failed to store image {image.filename}: {str(e)}"}), 500

    return jsonify({"urls": uploaded_urls})

@property_bp.route('/convert-telegram-images', methods=['POST'])
@token_required
def convert_telegram_images(current_user):
    data = request.get_json()
    image_urls = data.get('image_urls', [])
    
    converted_urls = []
    for url in image_urls:
        if url.startswith("AgACAgQAAxkBAAI") or len(url) > 50:
             converted_urls.append(f"https://via.placeholder.com/400x300?text=Telegram+Image")
        else:
            converted_urls.append(url)
            
    return jsonify({"converted_urls": converted_urls})


# -------------------------
# Car Endpoints
# -------------------------
@car_bp.route('/', methods=['GET'])
def find_cars_endpoint():
    args = request.args
    
    def get_val(key, type_func):
        val = args.get(key)
        if val is None: return None
        try: return type_func(val)
        except: return None

    try:
        car_type_val = args.get('car_type')
        filters = CarFilter(
            car_type=CarType(car_type_val) if car_type_val else None,
            min_price=get_val('min_price', float),
            max_price=get_val('max_price', float)
        )
        cars = property_use_cases.find_cars(filters)
        return jsonify([c.dict() for c in cars])
    except Exception as e:
         return jsonify({"detail": str(e)}), 400

@car_bp.route('/me', methods=['GET'])
@token_required
def get_my_cars(current_user):
    if UserRole.BROKER not in current_user.roles:
        return jsonify({"detail": "Only brokers can view their car listings"}), 403
    
    cars = property_use_cases.get_cars_by_broker(current_user.uid)
    return jsonify([c.dict() for c in cars])

@car_bp.route('/', methods=['POST'])
@token_required
def submit_car_endpoint(current_user):
    if UserRole.BROKER not in current_user.roles:
        return jsonify({"detail": "Only brokers can submit cars"}), 403
    
    data = request.get_json()
    try:
        car_data = CarCreate(**data)
        car_data.broker_id = current_user.uid
        car_data.broker_name = current_user.display_name or current_user.phone_number
        car_data.broker_phone = current_user.phone_number
        
        car = property_use_cases.submit_car(car_data)
        return jsonify(car.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@car_bp.route('/<car_id>', methods=['GET'])
def get_car_by_id_endpoint(car_id):
    try:
        car = property_use_cases.get_car_details(car_id)
        return jsonify(car.dict())
    except Exception as e:
        return jsonify({"detail": str(e)}), 404

@car_bp.route('/upload-images', methods=['POST'])
@token_required
def upload_car_images(current_user):
    if 'images' not in request.files:
         return jsonify({"detail": "No images provided"}), 400
    
    files = request.files.getlist('images')
    if not files:
         return jsonify({"detail": "No images provided"}), 400

    repo = getattr(property_use_cases, 'repo', None)
    if not repo or not hasattr(repo, 'save_image_blob'):
         return jsonify({"detail": "Image storage not available"}), 500

    uploaded_urls = []
    for image in files:
        if not image.content_type or not image.content_type.startswith('image/'):
             return jsonify({"detail": f"File {image.filename} is not an image"}), 400
        
        content = image.read()
        image_id = uuid.uuid4().hex
        content_type = image.content_type
        try:
            repo.save_image_blob(image_id=image_id, content_type=content_type, data=content)
            uploaded_urls.append(f"/images/{image_id}")
        except Exception as e:
            return jsonify({"detail": f"Failed to store image {image.filename}: {str(e)}"}), 500

    return jsonify({"urls": uploaded_urls})