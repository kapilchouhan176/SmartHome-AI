-- =========================================================
-- SmartHome AI - Database Schema
-- Run with:  mysql -u root -p < database/schema.sql
-- WARNING: this drops and recreates home_service_db.
-- =========================================================

DROP DATABASE IF EXISTS home_service_db;
CREATE DATABASE home_service_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE home_service_db;

-- ---------------------------------------------------------
-- 1. users : one login table for customers, providers, admins
-- ---------------------------------------------------------
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone         VARCHAR(15),
    role          ENUM('customer', 'provider', 'admin') NOT NULL DEFAULT 'customer',
    city          VARCHAR(60),
    address       VARCHAR(255),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role)
);

-- ---------------------------------------------------------
-- 2. services : the home service categories
-- ---------------------------------------------------------
CREATE TABLE services (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(60) NOT NULL UNIQUE,
    description VARCHAR(255),
    icon        VARCHAR(50) NOT NULL DEFAULT 'bi-tools',   -- Bootstrap icon class
    base_price  DECIMAL(10,2) NOT NULL DEFAULT 0,          -- starting price in ₹
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- 3. providers : extra profile details for provider users
-- ---------------------------------------------------------
CREATE TABLE providers (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL UNIQUE,
    bio                 VARCHAR(500),
    experience_years    INT NOT NULL DEFAULT 0,
    city                VARCHAR(60) NOT NULL,
    verification_status ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'pending',
    is_available        BOOLEAN NOT NULL DEFAULT TRUE,
    avg_rating          DECIMAL(3,2) NOT NULL DEFAULT 0,
    total_reviews       INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_providers_city_status (city, verification_status)
);

-- ---------------------------------------------------------
-- 4. provider_services : which services a provider offers + their price
-- ---------------------------------------------------------
CREATE TABLE provider_services (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    service_id  INT NOT NULL,
    charge      DECIMAL(10,2) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_provider_service (provider_id, service_id),
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id)  REFERENCES services(id)  ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- 5. bookings
-- ---------------------------------------------------------
CREATE TABLE bookings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT NOT NULL,
    provider_id         INT NOT NULL,
    service_id          INT NOT NULL,
    booking_date        DATE NOT NULL,
    time_slot           TIME NOT NULL,
    address             VARCHAR(255) NOT NULL,
    city                VARCHAR(60) NOT NULL,
    problem_description VARCHAR(1000),
    is_urgent           BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_cost      DECIMAL(10,2) NOT NULL,
    status              ENUM('pending', 'accepted', 'rejected',
                             'in_progress', 'completed', 'cancelled')
                        NOT NULL DEFAULT 'pending',
    cancel_reason       VARCHAR(255),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Double-booking guard:
    -- is 1 while the booking holds the slot, NULL once rejected/cancelled/completed.
    -- MySQL allows many NULLs in a UNIQUE index, so freed slots can be rebooked,
    -- but two active bookings for the same provider + date + slot are blocked.
    active_slot TINYINT AS (
        CASE WHEN status IN ('pending', 'accepted', 'in_progress') THEN 1 ELSE NULL END
    ) STORED,
    UNIQUE KEY uq_provider_slot (provider_id, booking_date, time_slot, active_slot),

    FOREIGN KEY (customer_id) REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id)  REFERENCES services(id),
    INDEX idx_bookings_customer (customer_id),
    INDEX idx_bookings_status (status)
);

-- ---------------------------------------------------------
-- 6. reviews : one review per completed booking
-- ---------------------------------------------------------
CREATE TABLE reviews (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    booking_id           INT NOT NULL UNIQUE,
    customer_id          INT NOT NULL,
    provider_id          INT NOT NULL,
    rating               TINYINT NOT NULL,
    comment              VARCHAR(1000),
    sentiment            ENUM('positive', 'negative', 'neutral'),
    sentiment_confidence DECIMAL(5,2),
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
    FOREIGN KEY (booking_id)  REFERENCES bookings(id)  ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    INDEX idx_reviews_sentiment (sentiment)
);

-- ---------------------------------------------------------
-- 7. ai_predictions : log of service suggestions (for admin stats)
-- ---------------------------------------------------------
CREATE TABLE ai_predictions (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT,
    input_text           VARCHAR(1000) NOT NULL,
    predicted_service_id INT,
    confidence           DECIMAL(5,2),
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)              REFERENCES users(id)    ON DELETE SET NULL,
    FOREIGN KEY (predicted_service_id) REFERENCES services(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------
-- 8. notifications : in-app messages
-- ---------------------------------------------------------
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    message    VARCHAR(255) NOT NULL,
    link       VARCHAR(255),
    is_read    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user_read (user_id, is_read)
);

-- ---------------------------------------------------------
-- Sample service categories
-- ---------------------------------------------------------
INSERT INTO services (name, description, icon, base_price) VALUES
('Plumbing',                  'Leaking taps, blocked drains, pipe fitting and bathroom fixtures.', 'bi-droplet',           299),
('Electrical Repair',         'Wiring, switchboards, fans, lights and power issues.',             'bi-lightning-charge',  249),
('AC Repair and Maintenance', 'AC servicing, gas refill, cooling problems and installation.',     'bi-snow',              499),
('Home Cleaning',             'Deep cleaning, kitchen and bathroom cleaning, sofa cleaning.',     'bi-stars',             799),
('Appliance Repair',          'Washing machine, refrigerator, microwave and geyser repair.',     'bi-plug',              349),
('Painting',                  'Interior and exterior painting, wall touch-ups and waterproofing.','bi-palette',           1499),
('Carpentry',                 'Furniture repair, door and window fixing, new fittings.',         'bi-hammer',            299),
('Pest Control',              'Termite, cockroach, bed bug and general pest treatment.',         'bi-bug',               699);
