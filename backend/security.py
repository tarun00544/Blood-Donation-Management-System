"""Security utilities: role-based decorators, session helpers, password validation."""
from functools import wraps
from flask import session
from utils import ServiceError

def get_current_user():
    """Returns the current logged-in user info from session, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return {
        "user_id": user_id,
        "email": session.get("email"),
        "name": session.get("name"),
        "role": session.get("role"),
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            raise ServiceError("Authentication required. Please log in.", 401)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            raise ServiceError("Authentication required. Please log in as administrator.", 401)
        if session.get("role") != "admin":
            raise ServiceError("Access denied. Administrator privileges required.", 403)
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            raise ServiceError("Authentication required. Please log in.", 401)
        if session.get("role") not in ("user", "admin"):
            raise ServiceError("Access denied.", 403)
        return f(*args, **kwargs)
    return decorated_function

def validate_password_strength(password):
    """Validates that password meets security requirements: at least 6 characters."""
    if not password or len(password) < 6:
        raise ServiceError("Password must be at least 6 characters long", 400)
    return password
