import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pymysql
import pymysql.cursors
from src.domain.models.user_models import User, UserCreate, UserRole
from src.domain.models.property_models import Property, PropertyCreate, PropertyFilter, PropertyStatus
from src.domain.models.car_models import Car, CarCreate, CarFilter, CarStatus
from src.utils.exceptions import DatabaseError, UserNotFoundError, PropertyNotFoundError
from src.utils.auth_utils import hash_password
from src.utils.config import settings


class MySQLRealEstateRepository:
    def __init__(self):
        self._connection_params = {
            'host': settings.MYSQL_HOST,
            'port': settings.MYSQL_PORT,
            'user': settings.MYSQL_USER,
            'password': settings.MYSQL_PASSWORD,
            'db': settings.MYSQL_DATABASE,
            'charset': 'utf8mb4',
            'autocommit': True,
            'cursorclass': pymysql.cursors.DictCursor
        }

    def _get_connection(self):
        """Get a fresh connection."""
        try:
            return pymysql.connect(**self._connection_params)
        except Exception as e:
            raise DatabaseError(f"Failed to connect to MySQL: {e}")

    def _execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Execute a query and return results."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.lastrowid
        except Exception as e:
            raise DatabaseError(f"Query execution failed: {e}")
        finally:
            conn.close()

    # --- Image Blob Methods ---
    def _ensure_images_table(self):
        """Create images table if it does not exist."""
        create_table_sql = (
            """
            CREATE TABLE IF NOT EXISTS images (
                image_id VARCHAR(64) PRIMARY KEY,
                content_type VARCHAR(255) NOT NULL,
                data LONGBLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """
        )
        self._execute_query(create_table_sql)

    def save_image_blob(self, image_id: str, content_type: str, data: bytes) -> None:
        self._ensure_images_table()
        insert_sql = "INSERT INTO images (image_id, content_type, data) VALUES (%s, %s, %s)"
        self._execute_query(insert_sql, (image_id, content_type, data))

    def get_image_blob(self, image_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_images_table()
        select_sql = "SELECT content_type, data FROM images WHERE image_id = %s"
        return self._execute_query(select_sql, (image_id,), fetch_one=True)

    # --- User Methods ---
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                WHERE u.telegram_id = %s
                GROUP BY u.uid
            """
            result = self._execute_query(query, (telegram_id,), fetch_one=True)
            if result:
                roles = result['roles'].split(',') if result.get('roles') else []
                result['roles'] = [UserRole(role) for role in roles if role]
                return User(**result)
            return None
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting user by telegram_id: {e}")

    def get_user_by_id(self, uid: str) -> User:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                WHERE u.uid = %s
                GROUP BY u.uid
            """
            result = self._execute_query(query, (uid,), fetch_one=True)
            if not result:
                raise UserNotFoundError(identifier=uid)
            
            roles = result['roles'].split(',') if result.get('roles') else []
            result['roles'] = [UserRole(role) for role in roles if role]
            return User(**result)
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting user by ID: {e}")

    def get_user_by_phone_number(self, phone_number: str) -> Optional[User]:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                WHERE u.phone_number = %s
                GROUP BY u.uid
            """
            result = self._execute_query(query, (phone_number,), fetch_one=True)
            if result:
                roles = result['roles'].split(',') if result.get('roles') else []
                result['roles'] = [UserRole(role) for role in roles if role]
                return User(**result)
            return None
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting user by phone: {e}")

    def create_user(self, user_data: UserCreate) -> User:
        try:
            uid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            user_dict = {
                "uid": uid,
                "phone_number": user_data.phone_number,
                "telegram_id": user_data.telegram_id,
                "display_name": user_data.display_name,
                "language": user_data.language,
                "hashed_password": hash_password(user_data.password) if user_data.password else None,
                "active": True,
                "created_at": now,
                "updated_at": now
            }
            
            user_query = """
                INSERT INTO users (uid, phone_number, telegram_id, display_name, language, hashed_password, active, created_at, updated_at)
                VALUES (%(uid)s, %(phone_number)s, %(telegram_id)s, %(display_name)s, %(language)s, %(hashed_password)s, %(active)s, %(created_at)s, %(updated_at)s)
            """
            self._execute_query(user_query, user_dict)
            
            if user_data.roles:
                for role in user_data.roles:
                    role_query = "INSERT INTO user_roles (user_id, role) VALUES (%s, %s)"
                    self._execute_query(role_query, (uid, role.value))
            
            return self.get_user_by_id(uid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while creating user: {e}")

    def update_user(self, uid: str, updates: Dict[str, Any]) -> User:
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key != 'roles':
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if set_clauses:
                params.append(datetime.now(timezone.utc))
                params.append(uid)
                query = f"UPDATE users SET {', '.join(set_clauses)}, updated_at = %s WHERE uid = %s"
                self._execute_query(query, tuple(params))
            
            if 'roles' in updates:
                self._execute_query("DELETE FROM user_roles WHERE user_id = %s", (uid,))
                for role in updates['roles']:
                    role_query = "INSERT INTO user_roles (user_id, role) VALUES (%s, %s)"
                    self._execute_query(role_query, (uid, role.value if hasattr(role, 'value') else role))
            
            return self.get_user_by_id(uid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while updating user: {e}")

    def find_admin_user(self) -> Optional[User]:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                WHERE ur.role = 'admin'
                GROUP BY u.uid
                LIMIT 1
            """
            result = self._execute_query(query, fetch_one=True)
            if result:
                roles = result['roles'].split(',') if result.get('roles') else []
                result['roles'] = [UserRole(role) for role in roles if role]
                return User(**result)
            return None
        except Exception as e:
            raise DatabaseError(f"MySQL error while finding admin user: {e}")

    def find_unclaimed_admin(self) -> Optional[User]:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                WHERE ur.role = 'admin' AND u.telegram_id = 0
                GROUP BY u.uid
                LIMIT 1
            """
            result = self._execute_query(query, fetch_one=True)
            if result:
                roles = result['roles'].split(',') if result.get('roles') else []
                result['roles'] = [UserRole(role) for role in roles if role]
                return User(**result)
            return None
        except Exception as e:
            raise DatabaseError(f"MySQL error while finding unclaimed admin: {e}")

    def list_users(self) -> List[User]:
        try:
            query = """
                SELECT u.*, GROUP_CONCAT(ur.role) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.uid = ur.user_id
                GROUP BY u.uid
            """
            results = self._execute_query(query, fetch_all=True)
            users = []
            for result in results:
                roles = result['roles'].split(',') if result.get('roles') else []
                result['roles'] = [UserRole(role) for role in roles if role]
                users.append(User(**result))
            return users
        except Exception as e:
            raise DatabaseError(f"MySQL error while listing users: {e}")

    def set_user_role(self, uid: str, role: UserRole, enable: bool) -> User:
        user = self.get_user_by_id(uid)
        roles = set(user.roles or [])
        if enable:
            roles.add(role)
        else:
            roles.discard(role)
        return self.update_user(uid, {"roles": list(roles)})

    def set_user_active(self, uid: str, active: bool) -> User:
        return self.update_user(uid, {"active": active})

    def delete_user(self, uid: str) -> None:
        try:
            self._execute_query("DELETE FROM users WHERE uid = %s", (uid,))
        except Exception as e:
            raise DatabaseError(f"MySQL error while deleting user: {e}")

    # --- Property Methods ---
    def create_property(self, property_data: PropertyCreate) -> Property:
        try:
            pid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            prop_dict = {
                "pid": pid,
                "property_type": property_data.property_type.value,
                "location_region": property_data.location.region,
                "location_city": property_data.location.city,
                "location_site": property_data.location.site,
                "bedrooms": property_data.bedrooms,
                "bathrooms": property_data.bathrooms,
                "size_sqm": property_data.size_sqm,
                "price_etb": property_data.price_etb,
                "description": property_data.description,
                "furnishing_status": property_data.furnishing_status.value if property_data.furnishing_status else None,
                "condominium_scheme": property_data.condominium_scheme.value if property_data.condominium_scheme else None,
                "floor_level": property_data.floor_level,
                "debt_status": property_data.debt_status,
                "structure_type": property_data.structure_type,
                "plot_size_sqm": property_data.plot_size_sqm,
                "title_deed": property_data.title_deed,
                "kitchen_type": property_data.kitchen_type,
                "living_rooms": property_data.living_rooms,
                "water_tank": property_data.water_tank,
                "parking_spaces": property_data.parking_spaces,
                "is_commercial": property_data.is_commercial,
                "total_floors": property_data.total_floors,
                "total_units": property_data.total_units,
                "has_elevator": property_data.has_elevator,
                "has_private_rooftop": property_data.has_private_rooftop,
                "is_two_story_penthouse": property_data.is_two_story_penthouse,
                "has_private_entrance": property_data.has_private_entrance,
                "broker_id": property_data.broker_id,
                "broker_name": property_data.broker_name,
                "broker_phone": property_data.broker_phone,
                "status": PropertyStatus.PENDING.value,
                "created_at": now,
                "updated_at": now
            }
            
            prop_query = """
                INSERT INTO properties (
                    pid, property_type, location_region, location_city, location_site,
                    bedrooms, bathrooms, size_sqm, price_etb, description,
                    furnishing_status, condominium_scheme, floor_level, debt_status,
                    structure_type, plot_size_sqm, title_deed, kitchen_type,
                    living_rooms, water_tank, parking_spaces, is_commercial,
                    total_floors, total_units, has_elevator, has_private_rooftop,
                    is_two_story_penthouse, has_private_entrance, broker_id,
                    broker_name, broker_phone, status, created_at, updated_at
                ) VALUES (
                    %(pid)s, %(property_type)s, %(location_region)s, %(location_city)s, %(location_site)s,
                    %(bedrooms)s, %(bathrooms)s, %(size_sqm)s, %(price_etb)s, %(description)s,
                    %(furnishing_status)s, %(condominium_scheme)s, %(floor_level)s, %(debt_status)s,
                    %(structure_type)s, %(plot_size_sqm)s, %(title_deed)s, %(kitchen_type)s,
                    %(living_rooms)s, %(water_tank)s, %(parking_spaces)s, %(is_commercial)s,
                    %(total_floors)s, %(total_units)s, %(has_elevator)s, %(has_private_rooftop)s,
                    %(is_two_story_penthouse)s, %(has_private_entrance)s, %(broker_id)s,
                    %(broker_name)s, %(broker_phone)s, %(status)s, %(created_at)s, %(updated_at)s
                )
            """
            self._execute_query(prop_query, prop_dict)
            
            for i, image_url in enumerate(property_data.image_urls):
                img_query = "INSERT INTO property_images (property_id, image_url, image_order) VALUES (%s, %s, %s)"
                self._execute_query(img_query, (pid, image_url, i))
            
            return self.get_property_by_id(pid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while creating property: {e}")

    def get_property_by_id(self, pid: str) -> Property:
        try:
            prop_query = "SELECT * FROM properties WHERE pid = %s"
            prop_result = self._execute_query(prop_query, (pid,), fetch_one=True)
            if not prop_result:
                raise PropertyNotFoundError(identifier=pid)
            
            img_query = "SELECT image_url FROM property_images WHERE property_id = %s ORDER BY image_order"
            img_results = self._execute_query(img_query, (pid,), fetch_all=True)
            image_urls = [img['image_url'] for img in img_results]
            
            prop_dict = dict(prop_result)
            prop_dict['image_urls'] = image_urls
            prop_dict['location'] = {
                'region': prop_dict['location_region'],
                'city': prop_dict['location_city'],
                'site': prop_dict['location_site']
            }
            
            return Property(**prop_dict)
        except PropertyNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting property by ID: {e}")

    def update_property(self, pid: str, updates: Dict[str, Any]) -> Property:
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            
            if set_clauses:
                params.append(datetime.now(timezone.utc))
                params.append(pid)
                query = f"UPDATE properties SET {', '.join(set_clauses)}, updated_at = %s WHERE pid = %s"
                self._execute_query(query, tuple(params))
            
            return self.get_property_by_id(pid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while updating property: {e}")

    def get_properties_by_status(self, status: PropertyStatus) -> List[Property]:
        try:
            query = """
                SELECT p.*, GROUP_CONCAT(pi.image_url ORDER BY pi.image_order) as image_urls
                FROM properties p
                LEFT JOIN property_images pi ON p.pid = pi.property_id
                WHERE p.status = %s
                GROUP BY p.pid
            """
            results = self._execute_query(query, (status.value,), fetch_all=True)
            properties = []
            for result in results:
                prop_dict = dict(result)
                prop_dict['image_urls'] = result['image_urls'].split(',') if result.get('image_urls') else []
                prop_dict['location'] = {
                    'region': prop_dict['location_region'],
                    'city': prop_dict['location_city'],
                    'site': prop_dict['location_site']
                }
                properties.append(Property(**prop_dict))
            return properties
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting properties by status: {e}")

    def get_properties_by_broker_id(self, broker_id: str) -> List[Property]:
        try:
            query = """
                SELECT p.*, GROUP_CONCAT(pi.image_url ORDER BY pi.image_order) as image_urls
                FROM properties p
                LEFT JOIN property_images pi ON p.pid = pi.property_id
                WHERE p.broker_id = %s
                GROUP BY p.pid
            """
            results = self._execute_query(query, (broker_id,), fetch_all=True)
            properties = []
            for result in results:
                prop_dict = dict(result)
                prop_dict['image_urls'] = result['image_urls'].split(',') if result.get('image_urls') else []
                prop_dict['location'] = {
                    'region': prop_dict['location_region'],
                    'city': prop_dict['location_city'],
                    'site': prop_dict['location_site']
                }
                properties.append(Property(**prop_dict))
            return properties
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting properties by broker ID: {e}")

    def query_properties(self, filters: PropertyFilter) -> List[Property]:
        try:
            where_conditions = ["p.status = %s"]
            params = [filters.status.value if filters.status else PropertyStatus.APPROVED.value]
            
            if filters.property_type:
                where_conditions.append("p.property_type = %s")
                params.append(filters.property_type.value)
            if filters.min_bedrooms:
                where_conditions.append("p.bedrooms >= %s")
                params.append(filters.min_bedrooms)
            if filters.max_bedrooms:
                where_conditions.append("p.bedrooms <= %s")
                params.append(filters.max_bedrooms)
            if filters.location_region:
                where_conditions.append("p.location_region = %s")
                params.append(filters.location_region)
            if filters.location_site:
                where_conditions.append("p.location_site = %s")
                params.append(filters.location_site)
            if filters.min_price:
                where_conditions.append("p.price_etb >= %s")
                params.append(filters.min_price)
            if filters.max_price:
                where_conditions.append("p.price_etb <= %s")
                params.append(filters.max_price)
            if filters.filter_is_commercial is not None:
                where_conditions.append("p.is_commercial = %s")
                params.append(filters.filter_is_commercial)
            if filters.filter_has_elevator is not None:
                where_conditions.append("p.has_elevator = %s")
                params.append(filters.filter_has_elevator)
            if filters.filter_has_private_rooftop is not None:
                where_conditions.append("p.has_private_rooftop = %s")
                params.append(filters.filter_has_private_rooftop)
            if filters.filter_is_two_story_penthouse is not None:
                where_conditions.append("p.is_two_story_penthouse = %s")
                params.append(filters.filter_is_two_story_penthouse)
            if filters.filter_has_private_entrance is not None:
                where_conditions.append("p.has_private_entrance = %s")
                params.append(filters.filter_has_private_entrance)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT p.*, GROUP_CONCAT(pi.image_url ORDER BY pi.image_order) as image_urls
                FROM properties p
                LEFT JOIN property_images pi ON p.pid = pi.property_id
                WHERE {where_clause}
                GROUP BY p.pid
            """
            
            results = self._execute_query(query, tuple(params), fetch_all=True)
            properties = []
            for result in results:
                prop_dict = dict(result)
                prop_dict['image_urls'] = result['image_urls'].split(',') if result.get('image_urls') else []
                prop_dict['location'] = {
                    'region': prop_dict['location_region'],
                    'city': prop_dict['location_city'],
                    'site': prop_dict['location_site']
                }
                properties.append(Property(**prop_dict))
            
            if filters.min_floor_level is not None:
                properties = [
                    prop for prop in properties 
                    if prop.floor_level is not None and prop.floor_level >= filters.min_floor_level
                ]
            
            return properties
        except Exception as e:
            raise DatabaseError(f"MySQL error while querying properties: {e}")

    def delete_property(self, pid: str) -> None:
        try:
            self._execute_query("DELETE FROM properties WHERE pid = %s", (pid,))
        except Exception as e:
            raise DatabaseError(f"MySQL error while deleting property: {e}")

    def count_properties_by_status(self) -> dict[PropertyStatus, int]:
        try:
            counts = {}
            for status in PropertyStatus:
                query = "SELECT COUNT(*) as count FROM properties WHERE status = %s"
                result = self._execute_query(query, (status.value,), fetch_one=True)
                counts[status] = result['count']
            return counts
        except Exception as e:
            raise DatabaseError(f"MySQL error while counting properties: {e}")

    # --- Car Methods ---
    def create_car(self, car_data: CarCreate) -> Car:
        try:
            cid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            car_dict = {
                "cid": cid,
                "car_type": car_data.car_type.value,
                "price_etb": car_data.price_etb,
                "manufacturer": car_data.manufacturer,
                "model_name": car_data.model_name,
                "model_year": car_data.model_year,
                "color": car_data.color,
                "plate": car_data.plate,
                "engine": car_data.engine,
                "power_hp": car_data.power_hp,
                "transmission": car_data.transmission,
                "fuel_efficiency_kmpl": car_data.fuel_efficiency_kmpl,
                "motor_type": car_data.motor_type,
                "mileage_km": car_data.mileage_km,
                "description": car_data.description,
                "broker_id": car_data.broker_id,
                "broker_name": car_data.broker_name,
                "broker_phone": car_data.broker_phone,
                "status": CarStatus.PENDING.value,
                "created_at": now,
                "updated_at": now
            }
            
            car_query = """
                INSERT INTO cars (
                    cid, car_type, price_etb, manufacturer, model_name, model_year,
                    color, plate, engine, power_hp, transmission, fuel_efficiency_kmpl,
                    motor_type, mileage_km, description, broker_id, broker_name,
                    broker_phone, status, created_at, updated_at
                ) VALUES (
                    %(cid)s, %(car_type)s, %(price_etb)s, %(manufacturer)s, %(model_name)s, %(model_year)s,
                    %(color)s, %(plate)s, %(engine)s, %(power_hp)s, %(transmission)s, %(fuel_efficiency_kmpl)s,
                    %(motor_type)s, %(mileage_km)s, %(description)s, %(broker_id)s, %(broker_name)s,
                    %(broker_phone)s, %(status)s, %(created_at)s, %(updated_at)s
                )
            """
            self._execute_query(car_query, car_dict)
            
            for i, image_url in enumerate(car_data.images):
                img_query = "INSERT INTO car_images (car_id, image_url, image_order) VALUES (%s, %s, %s)"
                self._execute_query(img_query, (cid, image_url, i))
            
            return self.get_car_by_id(cid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while creating car: {e}")

    def get_car_by_id(self, cid: str) -> Car:
        try:
            car_query = "SELECT * FROM cars WHERE cid = %s"
            car_result = self._execute_query(car_query, (cid,), fetch_one=True)
            if not car_result:
                raise PropertyNotFoundError(identifier=cid)
            
            img_query = "SELECT image_url FROM car_images WHERE car_id = %s ORDER BY image_order"
            img_results = self._execute_query(img_query, (cid,), fetch_all=True)
            images = [img['image_url'] for img in img_results]
            
            car_dict = dict(car_result)
            car_dict['images'] = images
            
            return Car(**car_dict)
        except PropertyNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting car by ID: {e}")

    def get_cars_by_broker_id(self, broker_id: str) -> List[Car]:
        try:
            query = """
                SELECT c.*, GROUP_CONCAT(ci.image_url ORDER BY ci.image_order) as images
                FROM cars c
                LEFT JOIN car_images ci ON c.cid = ci.car_id
                WHERE c.broker_id = %s
                GROUP BY c.cid
            """
            results = self._execute_query(query, (broker_id,), fetch_all=True)
            cars = []
            for result in results:
                car_dict = dict(result)
                car_dict['images'] = result['images'].split(',') if result.get('images') else []
                cars.append(Car(**car_dict))
            return cars
        except Exception as e:
            raise DatabaseError(f"MySQL error while getting cars by broker ID: {e}")

    def query_cars(self, filters: CarFilter) -> List[Car]:
        try:
            where_conditions = ["c.status = %s"]
            params = [CarStatus.APPROVED.value]
            
            if filters.car_type:
                where_conditions.append("c.car_type = %s")
                params.append(filters.car_type.value)
            if filters.min_price:
                where_conditions.append("c.price_etb >= %s")
                params.append(filters.min_price)
            if filters.max_price:
                where_conditions.append("c.price_etb <= %s")
                params.append(filters.max_price)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT c.*, GROUP_CONCAT(ci.image_url ORDER BY ci.image_order) as images
                FROM cars c
                LEFT JOIN car_images ci ON c.cid = ci.car_id
                WHERE {where_clause}
                GROUP BY c.cid
            """
            
            results = self._execute_query(query, tuple(params), fetch_all=True)
            cars = []
            for result in results:
                car_dict = dict(result)
                car_dict['images'] = result['images'].split(',') if result.get('images') else []
                cars.append(Car(**car_dict))
            return cars
        except Exception as e:
            raise DatabaseError(f"MySQL error while querying cars: {e}")

    def delete_car(self, cid: str) -> None:
        try:
            self._execute_query("DELETE FROM cars WHERE cid = %s", (cid,))
        except Exception as e:
            raise DatabaseError(f"MySQL error while deleting car: {e}")

    def update_car_status(self, cid: str, status: CarStatus) -> Car:
        try:
            query = "UPDATE cars SET status = %s, updated_at = %s WHERE cid = %s"
            self._execute_query(query, (status.value, datetime.now(timezone.utc), cid))
            return self.get_car_by_id(cid)
        except Exception as e:
            raise DatabaseError(f"MySQL error while updating car status: {e}")

    def list_all_cars(self) -> List[Car]:
        try:
            query = """
                SELECT c.*, GROUP_CONCAT(ci.image_url ORDER BY ci.image_order) as images
                FROM cars c
                LEFT JOIN car_images ci ON c.cid = ci.car_id
                GROUP BY c.cid
            """
            results = self._execute_query(query, fetch_all=True)
            cars = []
            for result in results:
                car_dict = dict(result)
                car_dict['images'] = result['images'].split(',') if result.get('images') else []
                cars.append(Car(**car_dict))
            return cars
        except Exception as e:
            raise DatabaseError(f"MySQL error while listing cars: {e}")

    def count_cars_by_status(self) -> dict[CarStatus, int]:
        try:
            counts = {}
            for status in CarStatus:
                query = "SELECT COUNT(*) as count FROM cars WHERE status = %s"
                result = self._execute_query(query, (status.value,), fetch_one=True)
                counts[status] = result['count']
            return counts
        except Exception as e:
            raise DatabaseError(f"MySQL error while counting cars: {e}")

    def close(self):
        """No-op for sync connection if not pooling, or implement if needed."""
        pass
