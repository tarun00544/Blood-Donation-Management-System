"""Authentication routes: registration, login, logout, and current user status."""
from flask import Blueprint, request

from services import auth_service
from utils import get_json_body, success, ServiceError

bp = Blueprint("auth", __name__)

@bp.post("/register")
def register():
    data = get_json_body()
    user = auth_service.register_user(data)
    return success("Registration successful! Welcome to BLOODCARE.", user, 201)

@bp.post("/login")
def login():
    data = get_json_body()
    user = auth_service.login_user(data)
    return success(f"Welcome back, {user['name']}!", user)

@bp.post("/admin-login")
def admin_login():
    data = get_json_body()
    user = auth_service.login_user(data, expected_role="admin")
    return success(f"Welcome to Admin Portal, {user['name']}!", user)

@bp.post("/logout")
def logout():
    auth_service.logout_user()
    return success("Logged out successfully")

@bp.get("/me")
def me():
    user = auth_service.get_session_user()
    if not user:
        raise ServiceError("Not logged in", 401)
    return success("Authenticated user details retrieved", user)
