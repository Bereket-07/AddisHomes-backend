-- MySQL Database Schema for Real Estate Platform
-- Compatible with cPanel MySQL databases

-- Create database (uncomment if needed)
-- CREATE DATABASE real_estate_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE real_estate_platform;

-- Users table
CREATE TABLE users (
    uid VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    telegram_id BIGINT NOT NULL DEFAULT 0,
    display_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    hashed_password VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_phone_number (phone_number),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_active (active)
);

-- User roles junction table (many-to-many relationship)
CREATE TABLE user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    role ENUM('buyer', 'broker', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (user_id, role),
    INDEX idx_user_id (user_id),
    INDEX idx_role (role)
);

-- Properties table
CREATE TABLE properties (
    pid VARCHAR(36) PRIMARY KEY,
    property_type ENUM('Apartment', 'Condominium', 'Villa', 'Building', 'Penthouse', 'Duplex') NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'sold') DEFAULT 'pending',
    
    -- Location
    location_region VARCHAR(100) NOT NULL,
    location_city VARCHAR(100) NOT NULL,
    location_site VARCHAR(100),
    
    -- Basic details
    bedrooms INT NOT NULL DEFAULT 0,
    bathrooms INT NOT NULL DEFAULT 0,
    size_sqm DECIMAL(10,2) NOT NULL,
    price_etb DECIMAL(15,2) NOT NULL,
    description TEXT NOT NULL,
    
    -- Optional features
    furnishing_status ENUM('Unfurnished', 'Semi-furnished', 'Fully-furnished'),
    condominium_scheme ENUM('20/80', '40/60', '10/90'),
    floor_level INT,
    debt_status VARCHAR(100),
    structure_type VARCHAR(100),
    plot_size_sqm DECIMAL(10,2),
    title_deed BOOLEAN DEFAULT FALSE,
    kitchen_type VARCHAR(100),
    living_rooms INT,
    water_tank BOOLEAN DEFAULT FALSE,
    parking_spaces INT DEFAULT 0,
    
    -- Building-specific features
    is_commercial BOOLEAN,
    total_floors INT,
    total_units INT,
    has_elevator BOOLEAN,
    
    -- Penthouse-specific features
    has_private_rooftop BOOLEAN,
    is_two_story_penthouse BOOLEAN,
    
    -- Duplex-specific features
    has_private_entrance BOOLEAN,
    
    -- Broker information
    broker_id VARCHAR(36),
    broker_name VARCHAR(255),
    broker_phone VARCHAR(20),
    
    -- Metadata
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key to users table
    FOREIGN KEY (broker_id) REFERENCES users(uid) ON DELETE SET NULL,
    
    -- Indexes for performance
    INDEX idx_property_type (property_type),
    INDEX idx_status (status),
    INDEX idx_location_region (location_region),
    INDEX idx_location_city (location_city),
    INDEX idx_location_site (location_site),
    INDEX idx_bedrooms (bedrooms),
    INDEX idx_price_etb (price_etb),
    INDEX idx_size_sqm (size_sqm),
    INDEX idx_broker_id (broker_id),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    
    -- Composite indexes for common queries
    INDEX idx_status_type (status, property_type),
    INDEX idx_location_query (location_region, location_city, location_site),
    INDEX idx_price_range (price_etb, bedrooms),
    INDEX idx_building_features (is_commercial, has_elevator),
    INDEX idx_penthouse_features (has_private_rooftop, is_two_story_penthouse),
    INDEX idx_duplex_features (has_private_entrance)
);

-- Property images table (one-to-many relationship)
CREATE TABLE property_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id VARCHAR(36) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    image_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (property_id) REFERENCES properties(pid) ON DELETE CASCADE,
    INDEX idx_property_id (property_id),
    INDEX idx_image_order (image_order)
);

-- Cars table
CREATE TABLE cars (
    cid VARCHAR(36) PRIMARY KEY,
    car_type ENUM('Sedan', 'Automobile', 'Van/Minivan', 'Pickup Truck', 'Electric/Hybrid', 'Luxury/Premium') NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'sold') DEFAULT 'pending',
    price_etb DECIMAL(15,2) NOT NULL,
    
    -- Basic car details
    manufacturer VARCHAR(100),
    model_name VARCHAR(100),
    model_year INT,
    color VARCHAR(50),
    plate VARCHAR(20),
    
    -- Technical specifications
    engine VARCHAR(100),
    power_hp INT,
    transmission VARCHAR(50),
    fuel_efficiency_kmpl DECIMAL(5,2),
    motor_type VARCHAR(50),
    mileage_km DECIMAL(10,2),
    
    -- Meta information
    description TEXT,
    
    -- Broker information
    broker_id VARCHAR(36),
    broker_name VARCHAR(255),
    broker_phone VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key to users table
    FOREIGN KEY (broker_id) REFERENCES users(uid) ON DELETE SET NULL,
    
    -- Indexes for performance
    INDEX idx_car_type (car_type),
    INDEX idx_status (status),
    INDEX idx_price_etb (price_etb),
    INDEX idx_manufacturer (manufacturer),
    INDEX idx_model_year (model_year),
    INDEX idx_broker_id (broker_id),
    INDEX idx_created_at (created_at),
    
    -- Composite indexes for common queries
    INDEX idx_status_type (status, car_type),
    INDEX idx_price_range (price_etb, car_type)
);

-- Car images table (one-to-many relationship)
CREATE TABLE car_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    car_id VARCHAR(36) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    image_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (car_id) REFERENCES cars(cid) ON DELETE CASCADE,
    INDEX idx_car_id (car_id),
    INDEX idx_image_order (image_order)
);

-- Create views for easier querying
CREATE VIEW active_users AS
SELECT u.*, GROUP_CONCAT(ur.role) as roles
FROM users u
LEFT JOIN user_roles ur ON u.uid = ur.user_id
WHERE u.active = TRUE
GROUP BY u.uid;

CREATE VIEW approved_properties AS
SELECT p.*, 
       GROUP_CONCAT(pi.image_url ORDER BY pi.image_order) as image_urls
FROM properties p
LEFT JOIN property_images pi ON p.pid = pi.property_id
WHERE p.status = 'approved'
GROUP BY p.pid;

CREATE VIEW approved_cars AS
SELECT c.*,
       GROUP_CONCAT(ci.image_url ORDER BY ci.image_order) as images
FROM cars c
LEFT JOIN car_images ci ON c.cid = ci.car_id
WHERE c.status = 'approved'
GROUP BY c.cid;

-- Insert default admin user (you can modify this)
INSERT INTO users (uid, phone_number, telegram_id, display_name, language, active) 
VALUES ('admin-default', '+251900000000', 0, 'System Admin', 'en', TRUE);

INSERT INTO user_roles (user_id, role) 
VALUES ('admin-default', 'admin');
