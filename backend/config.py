"""All settings are read from the .env file (or real environment variables).
No password is ever written inside the source code."""
import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    BASE_DIR = BASE_DIR

    # Flask Security & Session
    SECRET_KEY = os.getenv("SECRET_KEY", "bloodcare-super-secret-key-prod-2026-auth")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days in seconds

    # MySQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "blood_donation_system")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

    # Flask server
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # CORS (which frontends may call the API)
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

    # Business rules
    LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
    EXPIRING_SOON_DAYS = int(os.getenv("EXPIRING_SOON_DAYS", "7"))
    DONATION_GAP_DAYS = 90  # a donor can donate again after 90 days
