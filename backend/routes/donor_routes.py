from flask import Blueprint, request

from security import admin_required, login_required
from services import donor_service
from utils import get_json_body, success

bp = Blueprint("donors", __name__)


@bp.get("/donors")
def list_donors():
    donors = donor_service.list_donors(request.args)  # supports ?blood_group=, ?search=, ?location=, ?eligible=true
    return success("Donors retrieved successfully", donors)


@bp.get("/donors/<int:donor_id>")
def get_donor(donor_id):
    return success("Donor retrieved successfully", donor_service.get_donor(donor_id))


@bp.post("/donors")
@admin_required
def add_donor():
    donor = donor_service.create_donor(get_json_body())
    return success("Donor added successfully", donor, 201)


@bp.put("/donors/<int:donor_id>")
@admin_required
def update_donor(donor_id):
    donor = donor_service.update_donor(donor_id, get_json_body())
    return success("Donor updated successfully", donor)


@bp.delete("/donors/<int:donor_id>")
@admin_required
def delete_donor(donor_id):
    donor_service.delete_donor(donor_id)
    return success("Donor deleted successfully")


@bp.get("/search-donors")
def search_donors():
    donors = donor_service.search_donors(request.args)  # ?blood_group=O%2B (required) &location= &eligible=true
    return success(f"{len(donors)} matching donor(s) found", donors)
