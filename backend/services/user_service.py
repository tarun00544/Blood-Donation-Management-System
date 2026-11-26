"""User service: handles user profile, donor registration, personal blood requests, and dashboard."""
from werkzeug.security import check_password_hash, generate_password_hash

import database
from config import Config
from security import validate_password_strength
from services import inventory_service
from utils import (
    BLOOD_GROUPS,
    ServiceError,
    clean_text,
    normalize_blood_group,
    parse_date,
    parse_int,
    validate_phone,
)

def get_profile(user_id):
    with database.db_cursor() as cur:
        cur.execute(
            "SELECT user_id, name, email, phone, role, is_active, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cur.fetchone()
        if not user:
            raise ServiceError("User not found", 404)
        return user

def update_profile(user_id, data):
    name = clean_text(data.get("name"), "Full name", 100, required=True)
    phone = validate_phone(data.get("phone"))

    with database.db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET name = %s, phone = %s WHERE user_id = %s",
            (name, phone, user_id),
        )
        # Also sync donor record if exists
        cur.execute("UPDATE donor SET name = %s, phone = %s WHERE user_id = %s", (name, phone, user_id))
        return get_profile(user_id)

def change_password(user_id, data):
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not current_password or not new_password:
        raise ServiceError("Current and new passwords are required", 400)
    if new_password != confirm_password:
        raise ServiceError("New passwords do not match", 400)

    validate_password_strength(new_password)

    with database.db_cursor(commit=True) as cur:
        cur.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password_hash"], current_password):
            raise ServiceError("Current password is incorrect", 400)

        new_hash = generate_password_hash(new_password)
        cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id))
    return True

# --- Donor Management for Current User ---
def get_donor_profile(user_id):
    with database.db_cursor() as cur:
        cur.execute(
            "SELECT donor_id, user_id, name, blood_group, phone, email, location, "
            "last_donation_date, age, is_available "
            "FROM donor WHERE user_id = %s",
            (user_id,),
        )
        return cur.fetchone()

def register_as_donor(user_id, data):
    blood_group = normalize_blood_group(data.get("blood_group"))
    age = parse_int(data.get("age"), "Age", minimum=18, required=False)
    if age and age > 65:
        raise ServiceError("Blood donors must typically be between 18 and 65 years old")
    location = clean_text(data.get("location"), "Location", 200)
    phone = validate_phone(data.get("phone"))
    last_donation = parse_date(data.get("last_donation_date"), "Last donation date")
    is_available = True if data.get("is_available") in (True, 1, "1", "true", "True") else False

    with database.db_cursor(commit=True) as cur:
        # Fetch user's info
        cur.execute("SELECT name, email, phone FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            raise ServiceError("User not found", 404)

        phone_to_use = phone or user["phone"]
        email_to_use = user["email"]
        name_to_use = user["name"]

        # Check if already registered as donor
        cur.execute("SELECT donor_id FROM donor WHERE user_id = %s", (user_id,))
        existing = cur.fetchone()
        if existing:
            # Update existing donor record
            cur.execute(
                "UPDATE donor SET blood_group = %s, age = %s, location = %s, phone = %s, "
                "last_donation_date = %s, is_available = %s WHERE donor_id = %s",
                (blood_group, age, location, phone_to_use, last_donation, is_available, existing["donor_id"]),
            )
            donor_id = existing["donor_id"]
        else:
            # Check if donor with same email or phone exists (from legacy data)
            cur.execute("SELECT donor_id FROM donor WHERE email = %s OR phone = %s", (email_to_use, phone_to_use))
            match = cur.fetchone()
            if match:
                cur.execute(
                    "UPDATE donor SET user_id = %s, blood_group = %s, age = %s, location = %s, "
                    "last_donation_date = %s, is_available = %s WHERE donor_id = %s",
                    (user_id, blood_group, age, location, last_donation, is_available, match["donor_id"]),
                )
                donor_id = match["donor_id"]
            else:
                cur.execute(
                    "INSERT INTO donor (user_id, name, blood_group, phone, email, location, age, last_donation_date, is_available) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, name_to_use, blood_group, phone_to_use, email_to_use, location, age, last_donation, is_available),
                )
                donor_id = cur.lastrowid

        cur.execute("SELECT * FROM donor WHERE donor_id = %s", (donor_id,))
        return cur.fetchone()

def update_donor_availability(user_id, is_available):
    with database.db_cursor(commit=True) as cur:
        cur.execute("UPDATE donor SET is_available = %s WHERE user_id = %s", (bool(is_available), user_id))
        if cur.rowcount == 0:
            raise ServiceError("No donor profile found for this user. Please register as a donor first.", 404)
        cur.execute("SELECT * FROM donor WHERE user_id = %s", (user_id,))
        return cur.fetchone()

# --- Blood Requests for Current User ---
def get_user_requests(user_id):
    with database.db_cursor() as cur:
        cur.execute(
            """
            SELECT r.request_id, r.blood_group, r.units_required, r.hospital_id,
                   h.name AS hospital_name, h.location AS hospital_location,
                   r.request_date, r.required_date, r.status, r.notes,
                   rec.name AS recipient_name
            FROM blood_request r
            LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
            LEFT JOIN recipient rec ON rec.recipient_id = r.recipient_id
            WHERE r.user_id = %s
            ORDER BY r.request_date DESC, r.request_id DESC
            """,
            (user_id,),
        )
        return cur.fetchall()

def create_user_request(user_id, data):
    blood_group = normalize_blood_group(data.get("blood_group"))
    units_required = parse_int(data.get("units_required"), "units_required", minimum=1)
    hospital_id = parse_int(data.get("hospital_id"), "hospital_id", minimum=1)
    required_date = parse_date(data.get("required_date"), "required_date")
    notes = clean_text(data.get("notes"), "notes", 500)
    patient_name = clean_text(data.get("patient_name"), "patient_name", 100)

    with database.db_cursor(commit=True) as cur:
        # Check hospital exists
        cur.execute("SELECT hospital_id, name FROM hospital WHERE hospital_id = %s", (hospital_id,))
        hosp = cur.fetchone()
        if not hosp:
            raise ServiceError(f"Hospital with id {hospital_id} does not exist", 404)

        # Get user details
        cur.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        name_for_recipient = patient_name or user["name"]

        # Create or find a recipient entry for this user/patient
        cur.execute(
            "INSERT INTO recipient (name, blood_group, hospital_id, required_units) "
            "VALUES (%s, %s, %s, %s)",
            (name_for_recipient, blood_group, hospital_id, units_required),
        )
        recipient_id = cur.lastrowid

        # Insert blood_request linked to both recipient_id and user_id
        cur.execute(
            """
            INSERT INTO blood_request (recipient_id, blood_group, units_required, hospital_id, status, user_id, required_date, notes)
            VALUES (%s, %s, %s, %s, 'Pending', %s, %s, %s)
            """,
            (recipient_id, blood_group, units_required, hospital_id, user_id, required_date, notes),
        )
        request_id = cur.lastrowid

        cur.execute(
            """
            SELECT r.request_id, r.blood_group, r.units_required, r.hospital_id,
                   h.name AS hospital_name, r.request_date, r.required_date, r.status, r.notes,
                   rec.name AS recipient_name
            FROM blood_request r
            LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
            LEFT JOIN recipient rec ON rec.recipient_id = r.recipient_id
            WHERE r.request_id = %s
            """,
            (request_id,),
        )
        return cur.fetchone()

# --- User Dashboard Summary ---
def get_user_dashboard(user_id):
    with database.db_cursor() as cur:
        # User details
        cur.execute("SELECT user_id, name, email, phone, role, created_at FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        # Donor profile
        cur.execute("SELECT * FROM donor WHERE user_id = %s", (user_id,))
        donor = cur.fetchone()

        # Request counts
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END), 0) AS pending_requests,
                COALESCE(SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END), 0) AS approved_requests,
                COALESCE(SUM(CASE WHEN status = 'Fulfilled' THEN 1 ELSE 0 END), 0) AS fulfilled_requests,
                COALESCE(SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END), 0) AS rejected_requests
            FROM blood_request
            WHERE user_id = %s
            """,
            (user_id,),
        )
        request_stats = cur.fetchone()

        # Recent personal requests (limit 5)
        cur.execute(
            """
            SELECT r.request_id, r.blood_group, r.units_required, r.hospital_id,
                   h.name AS hospital_name, r.request_date, r.status
            FROM blood_request r
            LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
            WHERE r.user_id = %s
            ORDER BY r.request_date DESC LIMIT 5
            """,
            (user_id,),
        )
        recent_requests = cur.fetchall()

        # Blood availability overview
        inventory = inventory_service.inventory_by_group(cur)

    return {
        "user": user,
        "donor_profile": donor,
        "is_donor": donor is not None,
        "stats": request_stats,
        "recent_requests": recent_requests,
        "blood_availability": inventory,
    }

# --- User Notifications ---
def get_user_notifications(user_id):
    notifications = []
    with database.db_cursor() as cur:
        # Check blood request updates
        cur.execute(
            """
            SELECT r.request_id, r.blood_group, r.units_required, r.status, h.name AS hospital_name, r.request_date
            FROM blood_request r
            LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
            WHERE r.user_id = %s
            ORDER BY r.request_date DESC LIMIT 10
            """,
            (user_id,),
        )
        for req in cur.fetchall():
            if req["status"] == "Fulfilled":
                notifications.append({
                    "type": "success",
                    "title": "Blood Request Fulfilled!",
                    "message": f"Your request #{req['request_id']} for {req['units_required']} unit(s) of {req['blood_group']} at {req['hospital_name']} has been fulfilled.",
                    "date": req["request_date"]
                })
            elif req["status"] == "Approved":
                notifications.append({
                    "type": "info",
                    "title": "Blood Request Approved",
                    "message": f"Your request #{req['request_id']} for {req['units_required']} unit(s) of {req['blood_group']} has been approved. Awaiting issue from hospital.",
                    "date": req["request_date"]
                })
            elif req["status"] == "Rejected":
                notifications.append({
                    "type": "error",
                    "title": "Blood Request Rejected",
                    "message": f"Your request #{req['request_id']} for {req['units_required']} unit(s) of {req['blood_group']} could not be approved at this time.",
                    "date": req["request_date"]
                })
            else:
                notifications.append({
                    "type": "warning",
                    "title": "Blood Request Pending",
                    "message": f"Your request #{req['request_id']} for {req['units_required']} unit(s) of {req['blood_group']} is currently pending review.",
                    "date": req["request_date"]
                })

        # Donor eligibility check
        cur.execute("SELECT last_donation_date, is_available FROM donor WHERE user_id = %s", (user_id,))
        donor = cur.fetchone()
        if donor:
            if donor["last_donation_date"]:
                from datetime import date, timedelta
                gap = (date.today() - donor["last_donation_date"]).days
                if gap >= Config.DONATION_GAP_DAYS:
                    notifications.append({
                        "type": "success",
                        "title": "Eligible to Donate Blood",
                        "message": f"It has been {gap} days since your last donation. You are eligible to donate blood and save lives!",
                        "date": None
                    })
            else:
                notifications.append({
                    "type": "info",
                    "title": "Ready for First Blood Donation",
                    "message": "You are registered as a blood donor and ready to save lives today!",
                    "date": None
                })

    return notifications
