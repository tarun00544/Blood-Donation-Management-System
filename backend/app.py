"""Blood Donation Management System (BLOODCARE) - Flask backend.
Run with:  python app.py
"""
import logging
import os
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from flask import Flask, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from database import db_cursor, init_db
from migrate_db import run_migration
from routes.admin_routes import bp as admin_bp
from routes.auth_routes import bp as auth_bp
from routes.dashboard_routes import bp as dashboard_bp
from routes.donor_routes import bp as donor_bp
from routes.hospital_routes import bp as hospital_bp
from routes.inventory_routes import bp as inventory_bp
from routes.recipient_routes import bp as recipient_bp
from routes.report_routes import bp as report_bp
from routes.request_routes import bp as request_bp
from routes.user_routes import bp as user_bp
from utils import ServiceError, error_response, success

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

FRONTEND_DIR = os.path.abspath(os.path.join(Config.BASE_DIR, "..", "frontend"))


class JSONProvider(DefaultJSONProvider):
    """Sends dates as 'YYYY-MM-DD' / ISO text and MySQL decimals as plain numbers."""
    sort_keys = False

    @staticmethod
    def default(o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return DefaultJSONProvider.default(o)


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.json = JSONProvider(app)

    # Session & Security Settings
    app.secret_key = Config.SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = Config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = Config.SESSION_COOKIE_SAMESITE
    app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
    app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME

    # CORS: enables credentials (cookies/session) for frontend calls
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)

    # Register API Blueprints with their respective URL prefixes
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(donor_bp, url_prefix="/api")
    app.register_blueprint(hospital_bp, url_prefix="/api")
    app.register_blueprint(recipient_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")
    app.register_blueprint(request_bp, url_prefix="/api")

    # Automatic database initialization & migration
    try:
        init_db()
        run_migration()
        app.logger.info("Database '%s' and BLOODCARE tables are up to date.", Config.DB_NAME)
    except Exception as exc:
        app.logger.error("DATABASE SETUP FAILED: %s  -> check MySQL is running and .env is correct.", exc)

    @app.get("/api/health")
    def health():
        with db_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        return success("API and database connection are working", {"brand": "BLOODCARE", "status": "healthy"})

    # ---------- Serve Frontend Files ----------
    @app.get("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def serve_static(filename):
        target = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(target):
            return send_from_directory(FRONTEND_DIR, filename)
        if os.path.isdir(target):
            index_path = os.path.join(target, "index.html")
            if os.path.isfile(index_path):
                return send_from_directory(target, "index.html")
        return send_from_directory(FRONTEND_DIR, "index.html")

    # ---------- Consistent JSON Errors for APIs ----------
    @app.errorhandler(ServiceError)
    def handle_service_error(exc):
        return error_response(exc.message, exc.status_code)

    @app.errorhandler(mysql.connector.IntegrityError)
    def handle_integrity_error(exc):
        if exc.errno == 1062:
            return error_response("A record with the same unique value (email or phone) already exists", 409)
        if exc.errno == 1452:
            return error_response("A referenced record does not exist (check hospital_id / recipient_id)", 400)
        if exc.errno == 1451:
            return error_response("Cannot delete this record because other records depend on it", 400)
        return error_response("Invalid data: a database rule was violated", 400)

    @app.errorhandler(mysql.connector.Error)
    def handle_database_error(exc):
        app.logger.error("Database error: %s", exc)
        return error_response("A database error occurred. Please try again later.", 500)

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        messages = {404: "Endpoint not found", 405: "Method not allowed for this endpoint"}
        return error_response(messages.get(exc.code, exc.description), exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.exception("Unexpected error")
        return error_response("Internal server error", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=Config.DEBUG)
