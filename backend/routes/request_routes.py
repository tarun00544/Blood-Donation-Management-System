from flask import Blueprint, request

from security import admin_required, login_required
from services import request_service
from utils import ServiceError, get_json_body, parse_int, success

bp = Blueprint("requests", __name__)


@bp.get("/blood-requests")
@admin_required
def list_requests():
    # filters: ?status=Pending  ?blood_group=A%2B  ?hospital_id=1  ?recipient_id=2
    return success("Blood requests retrieved successfully", request_service.list_requests(request.args))


@bp.get("/blood-requests/<int:request_id>")
@login_required
def get_request(request_id):
    return success("Blood request retrieved successfully", request_service.get_request(request_id))


@bp.post("/blood-requests")
@login_required
def add_request():
    return success("Blood request created successfully", request_service.create_request(get_json_body()), 201)


@bp.put("/blood-requests/<int:request_id>")
@admin_required
def update_request(request_id):
    return success("Blood request updated successfully",
                   request_service.update_request(request_id, get_json_body()))


@bp.delete("/blood-requests/<int:request_id>")
@admin_required
def delete_request(request_id):
    request_service.delete_request(request_id)
    return success("Blood request deleted successfully")


# ---- Blood issue (transaction) ----
@bp.post("/blood-requests/<int:request_id>/issue")
@admin_required
def issue_blood(request_id):
    result = request_service.issue_blood(request_id)
    return success("Blood issued successfully and request marked as Fulfilled", result)


@bp.post("/issue-blood")
@admin_required
def issue_blood_by_body():
    """Same operation, with the request id in the JSON body: {"request_id": 2}"""
    request_id = parse_int(get_json_body().get("request_id"), "request_id", minimum=1)
    result = request_service.issue_blood(request_id)
    return success("Blood issued successfully and request marked as Fulfilled", result)
