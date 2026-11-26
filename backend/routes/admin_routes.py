"""Admin routes: user management, role verification, and system administration."""
from flask import Blueprint, session

import database
from security import admin_required
from utils import ServiceError, clean_text, get_json_body, success

bp = Blueprint("admin", __name__)

@bp.get("/users")
@admin_required
def list_users():
    """List all registered users with activity metrics. Password hashes are strictly omitted."""
    with database.db_cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.name, u.email, u.phone, u.role, u.is_active, u.created_at,
                   d.donor_id, d.blood_group AS donor_blood_group,
                   (SELECT COUNT(*) FROM blood_request WHERE user_id = u.user_id) AS request_count
            FROM users u
            LEFT JOIN donor d ON d.user_id = u.user_id
            ORDER BY u.user_id ASC
            """
        )
        users = cur.fetchall()
    return success("Users retrieved successfully", users)

@bp.put("/users/<int:user_id>/status")
@admin_required
def update_user_status(user_id):
    """Activates or deactivates a user account."""
    if user_id == session.get("user_id"):
        raise ServiceError("You cannot deactivate your own administrative account.", 400)

    body = get_json_body()
    is_active = body.get("is_active")
    if is_active is None:
        raise ServiceError("is_active boolean field is required", 400)

    is_active_val = bool(is_active)
    with database.db_cursor(commit=True) as cur:
        cur.execute("SELECT user_id, name, email, role FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            raise ServiceError(f"User with id {user_id} not found", 404)

        cur.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (is_active_val, user_id))
        user["is_active"] = is_active_val

    status_str = "activated" if is_active_val else "deactivated"
    return success(f"User account {status_str} successfully", user)
