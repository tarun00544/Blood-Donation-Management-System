"""Business logic for donors: validation, duplicate checks, SQL."""
from datetime import date, timedelta

from config import Config
from database import db_cursor
from utils import (ServiceError, clean_text, normalize_blood_group, parse_bool, parse_date,
                   validate_email, validate_phone)

COLUMNS = "donor_id, name, blood_group, phone, email, location, last_donation_date, is_available, age, user_id"


def _add_eligibility(row):
    last = row.get("last_donation_date")
    row["eligible_to_donate"] = last is None or (date.today() - last).days >= Config.DONATION_GAP_DAYS
    return row


def _validate(data):
    """Checks every field and returns clean values. Used by both POST and PUT."""
    clean = {
        "name": clean_text(data.get("name"), "name", 100, required=True),
        "blood_group": normalize_blood_group(data.get("blood_group")),
        "phone": validate_phone(data.get("phone")),
        "email": validate_email(data.get("email")),
        "location": clean_text(data.get("location"), "location", 200),
        "last_donation_date": parse_date(data.get("last_donation_date"), "last_donation_date"),
    }
    if clean["last_donation_date"] and clean["last_donation_date"] > date.today():
        raise ServiceError("last_donation_date cannot be in the future")
    if not clean["phone"] and not clean["email"]:
        raise ServiceError("Provide at least one contact: phone or email")
    return clean


def _check_duplicates(cur, clean, exclude_id=None):
    for column in ("email", "phone"):  # fixed names, not user input
        value = clean[column]
        if value is None:
            continue
        sql = f"SELECT donor_id FROM donor WHERE {column} = %s"
        params = [value]
        if exclude_id is not None:
            sql += " AND donor_id <> %s"
            params.append(exclude_id)
        cur.execute(sql, params)
        if cur.fetchone():
            raise ServiceError(f"A donor with this {column} already exists", 409)


def _fetch(cur, donor_id):
    cur.execute(f"SELECT {COLUMNS} FROM donor WHERE donor_id = %s", (donor_id,))
    row = cur.fetchone()
    if row is None:
        raise ServiceError("Donor not found", 404)
    return _add_eligibility(row)


def _filters(args):
    where, params = [], []
    if args.get("blood_group"):
        where.append("blood_group = %s")
        params.append(normalize_blood_group(args.get("blood_group")))
    search = (args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        where.append("(name LIKE %s OR email LIKE %s OR phone LIKE %s OR location LIKE %s)")
        params.extend([like, like, like, like])
    location = (args.get("location") or "").strip()
    if location:
        where.append("location LIKE %s")
        params.append(f"%{location}%")
    if parse_bool(args.get("eligible")):
        where.append("(last_donation_date IS NULL OR last_donation_date <= %s)")
        params.append(date.today() - timedelta(days=Config.DONATION_GAP_DAYS))
    return where, params


def list_donors(args):
    where, params = _filters(args)
    sql = f"SELECT {COLUMNS} FROM donor"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY donor_id"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [_add_eligibility(r) for r in cur.fetchall()]


def search_donors(args):
    """Used by /api/search-donors - blood_group is mandatory here."""
    normalize_blood_group(args.get("blood_group"))  # raises 400 if missing/invalid
    where, params = _filters(args)
    sql = (f"SELECT {COLUMNS} FROM donor WHERE " + " AND ".join(where) +
           " ORDER BY (last_donation_date IS NULL) DESC, last_donation_date ASC, name")
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [_add_eligibility(r) for r in cur.fetchall()]


def get_donor(donor_id):
    with db_cursor() as cur:
        return _fetch(cur, donor_id)


def create_donor(body):
    clean = _validate(body)
    with db_cursor(commit=True) as cur:
        _check_duplicates(cur, clean)
        cur.execute(
            "INSERT INTO donor (name, blood_group, phone, email, location, last_donation_date) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (clean["name"], clean["blood_group"], clean["phone"], clean["email"],
             clean["location"], clean["last_donation_date"]),
        )
        return _fetch(cur, cur.lastrowid)


def update_donor(donor_id, body):
    with db_cursor(commit=True) as cur:
        cur.execute(f"SELECT {COLUMNS} FROM donor WHERE donor_id = %s FOR UPDATE", (donor_id,))
        existing = cur.fetchone()
        if existing is None:
            raise ServiceError("Donor not found", 404)
        clean = _validate({**existing, **body})  # fields not sent keep their old value
        _check_duplicates(cur, clean, exclude_id=donor_id)
        cur.execute(
            "UPDATE donor SET name=%s, blood_group=%s, phone=%s, email=%s, location=%s, "
            "last_donation_date=%s WHERE donor_id=%s",
            (clean["name"], clean["blood_group"], clean["phone"], clean["email"],
             clean["location"], clean["last_donation_date"], donor_id),
        )
        return _fetch(cur, donor_id)


def delete_donor(donor_id):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM donor WHERE donor_id = %s", (donor_id,))
        if cur.rowcount == 0:
            raise ServiceError("Donor not found", 404)
