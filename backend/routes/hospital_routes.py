from flask import Blueprint, request

from database import db_cursor
from security import admin_required
from utils import ServiceError, clean_text, get_json_body, success

bp = Blueprint("hospitals", __name__)

COLUMNS = "hospital_id, name, location, contact_person"


def _validate(data):
    return {
        "name": clean_text(data.get("name"), "name", 100, required=True),
        "location": clean_text(data.get("location"), "location", 200),
        "contact_person": clean_text(data.get("contact_person"), "contact_person", 100),
    }


def _fetch(cur, hospital_id):
    cur.execute(f"SELECT {COLUMNS} FROM hospital WHERE hospital_id = %s", (hospital_id,))
    row = cur.fetchone()
    if row is None:
        raise ServiceError("Hospital not found", 404)
    return row


def _check_duplicate(cur, clean, exclude_id=None):
    sql = "SELECT hospital_id FROM hospital WHERE name = %s AND location <=> %s"
    params = [clean["name"], clean["location"]]
    if exclude_id is not None:
        sql += " AND hospital_id <> %s"
        params.append(exclude_id)
    cur.execute(sql, params)
    if cur.fetchone():
        raise ServiceError("A hospital with the same name and location already exists", 409)


@bp.get("/hospitals")
def list_hospitals():
    sql, params = f"SELECT {COLUMNS} FROM hospital", []
    search = (request.args.get("search") or "").strip()
    if search:
        sql += " WHERE name LIKE %s OR location LIKE %s"
        params = [f"%{search}%", f"%{search}%"]
    with db_cursor() as cur:
        cur.execute(sql + " ORDER BY hospital_id", params)
        return success("Hospitals retrieved successfully", cur.fetchall())


@bp.get("/hospitals/<int:hospital_id>")
def get_hospital(hospital_id):
    with db_cursor() as cur:
        return success("Hospital retrieved successfully", _fetch(cur, hospital_id))


@bp.post("/hospitals")
@admin_required
def add_hospital():
    clean = _validate(get_json_body())
    with db_cursor(commit=True) as cur:
        _check_duplicate(cur, clean)
        cur.execute("INSERT INTO hospital (name, location, contact_person) VALUES (%s, %s, %s)",
                    (clean["name"], clean["location"], clean["contact_person"]))
        hospital = _fetch(cur, cur.lastrowid)
    return success("Hospital added successfully", hospital, 201)


@bp.put("/hospitals/<int:hospital_id>")
@admin_required
def update_hospital(hospital_id):
    body = get_json_body()
    with db_cursor(commit=True) as cur:
        existing = _fetch(cur, hospital_id)
        clean = _validate({**existing, **body})
        _check_duplicate(cur, clean, exclude_id=hospital_id)
        cur.execute("UPDATE hospital SET name=%s, location=%s, contact_person=%s WHERE hospital_id=%s",
                    (clean["name"], clean["location"], clean["contact_person"], hospital_id))
        hospital = _fetch(cur, hospital_id)
    return success("Hospital updated successfully", hospital)


@bp.delete("/hospitals/<int:hospital_id>")
@admin_required
def delete_hospital(hospital_id):
    with db_cursor(commit=True) as cur:
        _fetch(cur, hospital_id)
        cur.execute("DELETE FROM hospital WHERE hospital_id = %s", (hospital_id,))
    return success("Hospital deleted successfully (its stock and requests were removed too)")
