from flask import Blueprint

from database import db_cursor
from security import admin_required
from services import inventory_service, request_service
from utils import BLOOD_GROUPS, REQUEST_STATUSES, success

bp = Blueprint("reports", __name__)

VALID = "(s.expiry_date IS NULL OR s.expiry_date >= CURDATE())"


@bp.get("/donors-by-blood-group")
@admin_required
def donors_by_blood_group():
    with db_cursor() as cur:
        cur.execute("SELECT blood_group, COUNT(*) AS total_donors FROM donor GROUP BY blood_group")
        found = {r["blood_group"]: r["total_donors"] for r in cur.fetchall()}
    data = [{"blood_group": g, "total_donors": found.get(g, 0)} for g in BLOOD_GROUPS]
    return success("Donor count by blood group", data)


@bp.get("/inventory-by-blood-group")
@admin_required
def inventory_by_blood_group():
    with db_cursor() as cur:
        return success("Blood inventory by blood group", inventory_service.inventory_by_group(cur))


@bp.get("/hospital-inventory")
@admin_required
def hospital_inventory():
    with db_cursor() as cur:
        cur.execute(f"""
            SELECT h.hospital_id, h.name AS hospital_name, h.location, s.blood_group,
                   COALESCE(SUM(CASE WHEN {VALID} THEN s.units_available END), 0) AS units_available
            FROM hospital h
            LEFT JOIN blood_stock s ON s.hospital_id = h.hospital_id
            GROUP BY h.hospital_id, h.name, h.location, s.blood_group
            ORDER BY h.hospital_id, s.blood_group""")
        rows = cur.fetchall()
    hospitals = {}
    for r in rows:
        entry = hospitals.setdefault(r["hospital_id"], {
            "hospital_id": r["hospital_id"], "hospital_name": r["hospital_name"], "location": r["location"],
            "inventory": {g: 0 for g in BLOOD_GROUPS}, "total_units": 0})
        if r["blood_group"]:
            units = int(r["units_available"])
            entry["inventory"][r["blood_group"]] = units
            entry["total_units"] += units
    return success("Hospital inventory (valid units only)", list(hospitals.values()))


@bp.get("/total-stock")
@admin_required
def total_stock():
    with db_cursor() as cur:
        cur.execute(f"""
            SELECT COALESCE(SUM(CASE WHEN {VALID} THEN s.units_available END), 0) AS valid_units,
                   COALESCE(SUM(CASE WHEN s.expiry_date < CURDATE() THEN s.units_available END), 0) AS expired_units,
                   COUNT(*) AS total_batches
            FROM blood_stock s""")
        row = cur.fetchone()
    return success("Total blood stock", {k: int(v) for k, v in row.items()})


@bp.get("/request-statistics")
@admin_required
def request_statistics():
    with db_cursor() as cur:
        cur.execute("SELECT status, COUNT(*) AS total_requests, COALESCE(SUM(units_required), 0) AS total_units "
                    "FROM blood_request GROUP BY status")
        found = {r["status"]: r for r in cur.fetchall()}
    by_status = [{"status": s,
                  "total_requests": int(found[s]["total_requests"]) if s in found else 0,
                  "total_units": int(found[s]["total_units"]) if s in found else 0} for s in REQUEST_STATUSES]
    data = {"total_requests": sum(i["total_requests"] for i in by_status), "by_status": by_status}
    return success("Blood request statistics", data)


@bp.get("/pending-requests")
@admin_required
def pending_requests():
    rows = request_service.list_requests({"status": "Pending"})
    return success(f"{len(rows)} pending request(s)", rows)


@bp.get("/expired-stock")
@admin_required
def expired_stock():
    rows = inventory_service.list_stock({"expiry": "expired"})
    return success(f"{len(rows)} expired stock batch(es)", rows)
