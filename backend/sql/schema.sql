-- =====================================================================
-- BLOOD DONATION MANAGEMENT SYSTEM - database schema (MySQL 8.0.16+)
-- You can run this file by hand (MySQL Workbench / mysql CLI), or just
-- start the Flask app, which runs it automatically.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS blood_donation_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE blood_donation_system;

-- 1. DONOR --------------------------------------------------------------
-- email and phone are UNIQUE (NULL is allowed, and several NULLs are fine).
-- "location" is an optional extra column so donors can be searched by city.
CREATE TABLE IF NOT EXISTS donor (
    donor_id           INT AUTO_INCREMENT PRIMARY KEY,
    name               VARCHAR(100) NOT NULL,
    blood_group        VARCHAR(5)   NOT NULL,
    phone              VARCHAR(15),
    email              VARCHAR(100),
    location           VARCHAR(200),
    last_donation_date DATE,
    CONSTRAINT uq_donor_email UNIQUE (email),
    CONSTRAINT uq_donor_phone UNIQUE (phone),
    CONSTRAINT chk_donor_blood_group CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
    INDEX idx_donor_blood_group (blood_group),
    INDEX idx_donor_name (name),
    INDEX idx_donor_location (location)
) ENGINE=InnoDB;

-- 2. HOSPITAL -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital (
    hospital_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    location       VARCHAR(200),
    contact_person VARCHAR(100),
    INDEX idx_hospital_name (name)
) ENGINE=InnoDB;

-- 3. RECIPIENT ----------------------------------------------------------
-- If a hospital is deleted, its recipients are kept (hospital_id becomes NULL).
CREATE TABLE IF NOT EXISTS recipient (
    recipient_id   INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    blood_group    VARCHAR(5)   NOT NULL,
    hospital_id    INT,
    required_units INT,
    CONSTRAINT chk_recipient_units CHECK (required_units IS NULL OR required_units >= 0),
    CONSTRAINT fk_recipient_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital (hospital_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_recipient_blood_group (blood_group)
) ENGINE=InnoDB;

-- 4. BLOOD_STOCK --------------------------------------------------------
-- One row = one batch of blood of one group, in one hospital, with one expiry date.
-- Stock belongs to a hospital, so it is deleted together with the hospital.
CREATE TABLE IF NOT EXISTS blood_stock (
    stock_id        INT AUTO_INCREMENT PRIMARY KEY,
    blood_group     VARCHAR(5) NOT NULL,
    units_available INT        NOT NULL,
    expiry_date     DATE,
    hospital_id     INT,
    CONSTRAINT chk_stock_units CHECK (units_available >= 0),
    CONSTRAINT fk_stock_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital (hospital_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_stock_group_hospital (blood_group, hospital_id),
    INDEX idx_stock_expiry (expiry_date)
) ENGINE=InnoDB;

-- 5. BLOOD_REQUEST ------------------------------------------------------
-- status: Pending | Approved | Fulfilled | Rejected
CREATE TABLE IF NOT EXISTS blood_request (
    request_id     INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id   INT         NOT NULL,
    blood_group    VARCHAR(5)  NOT NULL,
    units_required INT         NOT NULL,
    hospital_id    INT         NOT NULL,
    request_date   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(30) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_request_units CHECK (units_required > 0),
    CONSTRAINT chk_request_status CHECK (status IN ('Pending','Approved','Fulfilled','Rejected')),
    CONSTRAINT fk_request_recipient FOREIGN KEY (recipient_id)
        REFERENCES recipient (recipient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_request_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital (hospital_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_request_status (status),
    INDEX idx_request_blood_group (blood_group),
    INDEX idx_request_date (request_date)
) ENGINE=InnoDB;
