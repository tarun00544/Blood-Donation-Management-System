"""Authentication service: handles user registration, login, session setup, and profile check."""
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

import database
from security import validate_password_strength
from utils import ServiceError, clean_text, validate_email, validate_phone

def register_user(data):
    """Registers a new regular user. Role is ALWAYS 'user'."""
    name = clean_text(data.get("name"), "Full name", 100, required=True)
    email = validate_email(data.get("email"))
    if not email:
        raise ServiceError("A valid email address is required", 400)
    phone = validate_phone(data.get("phone"))
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not password:
        raise ServiceError("Password is required", 400)
    if password != confirm_password:
        raise ServiceError("Passwords do not match", 400)

    validate_password_strength(password)
    password_hash = generate_password_hash(password)

    with database.db_cursor(commit=True) as cur:
        # Check if email is already registered
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            raise ServiceError("An account with this email already exists", 409)

        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash, role, is_active) "
            "VALUES (%s, %s, %s, %s, 'user', TRUE)",
            (name, email, phone, password_hash),
        )
        user_id = cur.lastrowid
        cur.execute(
            "SELECT user_id, name, email, phone, role, is_active, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cur.fetchone()

    # Automatically set session on registration
    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    session["email"] = user["email"]
    session["role"] = user["role"]
    session.permanent = True

    return user

def login_user(data, expected_role=None):
    """Authenticates a user by email and password. Optionally enforces expected_role (e.g. 'admin')."""
    email = validate_email(data.get("email"))
    password = data.get("password")

    if not email or not password:
        raise ServiceError("Email and password are required", 400)

    with database.db_cursor() as cur:
        cur.execute(
            "SELECT user_id, name, email, phone, password_hash, role, is_active, created_at "
            "FROM users WHERE email = %s",
            (email,),
        )
        user = cur.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        raise ServiceError("Invalid email or password", 401)

    if not user["is_active"]:
        raise ServiceError("Your account has been deactivated. Please contact an administrator.", 403)

    if expected_role and user["role"] != expected_role:
        if expected_role == "admin":
            raise ServiceError("Access denied. You do not have administrator permissions.", 403)
        # Note: If an admin logs in through user portal, they can proceed as a user/admin

    # Establish session
    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    session["email"] = user["email"]
    session["role"] = user["role"]
    session.permanent = True

    user_info = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "created_at": user["created_at"],
    }
    return user_info

def logout_user():
    session.clear()
    return True

def get_session_user():
    """Retrieves current user details from database using session user_id."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    with database.db_cursor() as cur:
        cur.execute(
            "SELECT user_id, name, email, phone, role, is_active, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cur.fetchone()
        if not user or not user["is_active"]:
            session.clear()
            return None
        return user
