"""User-specific routes for profile, personal blood requests, donor actions, and personal dashboard."""
from flask import Blueprint, session

from security import login_required
from services import user_service
from utils import get_json_body, success

bp = Blueprint("user", __name__)

@bp.get("/profile")
@login_required
def get_profile():
    user = user_service.get_profile(session["user_id"])
    return success("Profile retrieved successfully", user)

@bp.put("/profile")
@login_required
def update_profile():
    updated = user_service.update_profile(session["user_id"], get_json_body())
    session["name"] = updated["name"]
    return success("Profile updated successfully", updated)

@bp.put("/change-password")
@login_required
def change_password():
    user_service.change_password(session["user_id"], get_json_body())
    return success("Password updated successfully")

@bp.get("/donor-profile")
@login_required
def get_donor_profile():
    profile = user_service.get_donor_profile(session["user_id"])
    return success("Donor profile retrieved", profile)

@bp.post("/become-donor")
@login_required
def become_donor():
    donor = user_service.register_as_donor(session["user_id"], get_json_body())
    return success("Donor registration completed successfully!", donor, 201)

@bp.put("/donor-availability")
@login_required
def update_donor_availability():
    body = get_json_body()
    donor = user_service.update_donor_availability(session["user_id"], body.get("is_available"))
    return success("Donor availability status updated", donor)

@bp.get("/blood-requests")
@login_required
def get_blood_requests():
    requests = user_service.get_user_requests(session["user_id"])
    return success("User blood requests retrieved", requests)

@bp.post("/blood-requests")
@login_required
def create_blood_request():
    req = user_service.create_user_request(session["user_id"], get_json_body())
    return success("Blood request submitted successfully", req, 201)

@bp.get("/dashboard")
@login_required
def get_dashboard():
    data = user_service.get_user_dashboard(session["user_id"])
    return success("User dashboard data retrieved", data)

@bp.get("/notifications")
@login_required
def get_notifications():
    notifications = user_service.get_user_notifications(session["user_id"])
    return success("User notifications retrieved", notifications)
