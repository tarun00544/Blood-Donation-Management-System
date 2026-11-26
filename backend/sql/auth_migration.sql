-- =====================================================================
-- BLOODCARE: AUTHENTICATION AND ROLE-BASED ACCESS MIGRATION
-- Adds users table, links donors and blood_requests to users,
-- and inserts default administrator.
-- =====================================================================

USE blood_donation_system;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'user',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_role CHECK (role IN ('user', 'admin')),
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB;

-- Default Admin User (Password: Admin@123)
INSERT INTO users (name, email, phone, password_hash, role, is_active)
SELECT 'System Administrator', 'admin@bloodcare.com', '+919999988888',
       'scrypt:32768:8:1$M41AzGjfqjBYhR3U$f44262bf4137a4fd217fd3fc7793344122dd6403d0b48096371056236b8281b7724bbabe0188e16c5d045e5d4ef56a996f9b361c950c2863ed70cc736ea00382',
       'admin', TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@bloodcare.com');
