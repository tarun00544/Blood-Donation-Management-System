"""Admin dashboard route: aggregated real-time database statistics and visualizations data."""
from flask import Blueprint

from config import Config
from database import db_cursor
from security import admin_required
from services import inventory_service, request_service
from utils import BLOOD_GROUPS, success

bp = Blueprint("dashboard", __name__)

def _count(cur, table, where=""):
    sql = f"SELECT COUNT(*) AS total FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cur.execute(sql)
    return cur.fetchone()["total"]

@bp.get("/dashboard")
@admin_required
def dashboard():
    with db_cursor() as cur:
        inventory = inventory_service.inventory_by_group(cur)

        # Recent donors
        cur.execute(
            """
            SELECT donor_id, name, blood_group, phone, email, location, last_donation_date, is_available
            FROM donor ORDER BY donor_id DESC LIMIT 5
            """
        )
        recent_donors = cur.fetchall()

        # Recent requests
        cur.execute(request_service.REQUEST_SELECT + " ORDER BY r.request_date DESC, r.request_id DESC LIMIT 5")
        recent_requests = cur.fetchall()

        # Request status breakdown
        cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END), 0) AS approved,
                COALESCE(SUM(CASE WHEN status = 'Fulfilled' THEN 1 ELSE 0 END), 0) AS fulfilled,
                COALESCE(SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END), 0) AS rejected
            FROM blood_request
            """
        )
        req_counts = cur.fetchone()

        # Hospital-wise blood stock summary
        cur.execute(
            """
            SELECT h.hospital_id, h.name AS hospital_name,
                   COALESCE(SUM(CASE WHEN (s.expiry_date IS NULL OR s.expiry_date >= CURDATE()) THEN s.units_available END), 0) AS valid_units
            FROM hospital h
            LEFT JOIN blood_stock s ON s.hospital_id = h.hospital_id
            GROUP BY h.hospital_id, h.name
            ORDER BY valid_units DESC
            """
        )
        hospital_stock = cur.fetchall()

        # Donors by blood group breakdown
        cur.execute(
            """
            SELECT blood_group, COUNT(*) AS total
            FROM donor
            GROUP BY blood_group
            """
        )
        donor_groups_map = {r["blood_group"]: r["total"] for r in cur.fetchall()}
        donors_by_group = [{"blood_group": g, "count": donor_groups_map.get(g, 0)} for g in BLOOD_GROUPS]

        # Monthly donation count estimation (based on last_donation_date)
        cur.execute(
            """
            SELECT DATE_FORMAT(last_donation_date, '%%Y-%%m') AS month, COUNT(*) AS count
            FROM donor
            WHERE last_donation_date IS NOT NULL
            GROUP BY month
            ORDER BY month DESC LIMIT 6
            """
        )
        monthly_donations = cur.fetchall()

        # Low stock blood groups
        low_stock = inventory_service.low_stock_groups(inventory)

        data = {
            "total_donors": _count(cur, "donor"),
            "total_hospitals": _count(cur, "hospital"),
            "total_recipients": _count(cur, "recipient"),
            "total_blood_requests": _count(cur, "blood_request"),
            "total_blood_units": sum(i["units_available"] for i in inventory),
            "pending_requests": int(req_counts["pending"]),
            "approved_requests": int(req_counts["approved"]),
            "fulfilled_requests": int(req_counts["fulfilled"]),
            "rejected_requests": int(req_counts["rejected"]),
            "blood_inventory": [
                {"blood_group": i["blood_group"], "units_available": i["units_available"], "expired_units": i["expired_units"]}
                for i in inventory
            ],
            "donors_by_group": donors_by_group,
            "hospital_stock": hospital_stock,
            "monthly_donations": monthly_donations,
            "low_stock_threshold": Config.LOW_STOCK_THRESHOLD,
            "low_stock_blood_groups": low_stock,
            "recent_donors": recent_donors,
            "recent_requests": recent_requests,
        }
    return success("Dashboard data retrieved successfully", data)
