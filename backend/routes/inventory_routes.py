from flask import Blueprint, request

from security import admin_required
from services import inventory_service
from utils import get_json_body, success

bp = Blueprint("inventory", __name__)


@bp.get("/blood-stock")
def list_stock():
    # filters: ?blood_group=O%2B  ?hospital_id=1  ?expiry=expired|valid|expiring_soon
    return success("Blood stock retrieved successfully", inventory_service.list_stock(request.args))


@bp.get("/blood-stock/<int:stock_id>")
def get_stock(stock_id):
    return success("Blood stock retrieved successfully", inventory_service.get_stock(stock_id))


@bp.post("/blood-stock")
@admin_required
def add_stock():
    row, merged = inventory_service.create_stock(get_json_body())
    if merged:
        return success("Units added to the existing batch (same blood group, hospital and expiry date)", row, 200)
    return success("Blood stock added successfully", row, 201)


@bp.put("/blood-stock/<int:stock_id>")
@admin_required
def update_stock(stock_id):
    return success("Blood stock updated successfully", inventory_service.update_stock(stock_id, get_json_body()))


@bp.delete("/blood-stock/<int:stock_id>")
@admin_required
def delete_stock(stock_id):
    inventory_service.delete_stock(stock_id)
    return success("Blood stock deleted successfully")
