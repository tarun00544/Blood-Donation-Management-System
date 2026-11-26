from flask import Blueprint, request

from database import db_cursor, ensure_exists
from security import admin_required
from utils import (ServiceError, clean_text, get_json_body, normalize_blood_group, parse_int, success)

bp = Blueprint("recipients", __name__)

SELECT = """
SELECT r.recipient_id, r.name, r.blood_group, r.hospital_id, h.name AS hospital_name, r.required_units
FROM recipient r
LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
"""


def _validate(cur, data):
    clean = {
        "name": clean_text(data.get("name"), "name", 100, required=True),
        "blood_group": normalize_blood_group(data.get("blood_group")),
        "hospital_id": parse_int(data.get("hospital_id"), "hospital_id", minimum=1, required=False),
        "required_units": parse_int(data.get("required_units"), "required_units", minimum=1, required=False),
    }
    if clean["hospital_id"] is not None:
        ensure_exists(cur, "hospital", "hospital_id", clean["hospital_id"], "Hospital")
    return clean


def _fetch(cur, recipient_id):
    cur.execute(SELECT + " WHERE r.recipient_id = %s", (recipient_id,))
    row = cur.fetchone()
    if row is None:
        raise ServiceError("Recipient not found", 404)
    return row


@bp.get("/recipients")
@admin_required
def list_recipients():
    where, params = [], []
    if request.args.get("blood_group"):
        where.append("r.blood_group = %s")
        params.append(normalize_blood_group(request.args.get("blood_group")))
    if request.args.get("hospital_id"):
        where.append("r.hospital_id = %s")
        params.append(parse_int(request.args.get("hospital_id"), "hospital_id", minimum=1))
    search = (request.args.get("search") or "").strip()
    if search:
        where.append("r.name LIKE %s")
        params.append(f"%{search}%")
    sql = SELECT + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY r.recipient_id"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return success("Recipients retrieved successfully", cur.fetchall())


@bp.get("/recipients/<int:recipient_id>")
@admin_required
def get_recipient(recipient_id):
    with db_cursor() as cur:
        return success("Recipient retrieved successfully", _fetch(cur, recipient_id))


@bp.post("/recipients")
@admin_required
def add_recipient():
    body = get_json_body()
    with db_cursor(commit=True) as cur:
        clean = _validate(cur, body)
        cur.execute("INSERT INTO recipient (name, blood_group, hospital_id, required_units) VALUES (%s,%s,%s,%s)",
                    (clean["name"], clean["blood_group"], clean["hospital_id"], clean["required_units"]))
        recipient = _fetch(cur, cur.lastrowid)
    return success("Recipient added successfully", recipient, 201)


@bp.put("/recipients/<int:recipient_id>")
@admin_required
def update_recipient(recipient_id):
    body = get_json_body()
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT name, blood_group, hospital_id, required_units FROM recipient "
                    "WHERE recipient_id = %s FOR UPDATE", (recipient_id,))
        existing = cur.fetchone()
        if existing is None:
            raise ServiceError("Recipient not found", 404)
        clean = _validate(cur, {**existing, **body})
        cur.execute("UPDATE recipient SET name=%s, blood_group=%s, hospital_id=%s, required_units=%s "
                    "WHERE recipient_id=%s",
                    (clean["name"], clean["blood_group"], clean["hospital_id"], clean["required_units"],
                     recipient_id))
        recipient = _fetch(cur, recipient_id)
    return success("Recipient updated successfully", recipient)


@bp.delete("/recipients/<int:recipient_id>")
@admin_required
def delete_recipient(recipient_id):
    with db_cursor(commit=True) as cur:
        _fetch(cur, recipient_id)
        cur.execute("DELETE FROM recipient WHERE recipient_id = %s", (recipient_id,))
    return success("Recipient deleted successfully (their blood requests were removed too)")
