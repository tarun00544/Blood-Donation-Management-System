"""Helpers shared by all routes and services: JSON responses, errors, input validation."""
import re
from datetime import date, datetime

from flask import jsonify, request

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
REQUEST_STATUSES = ["Pending", "Approved", "Fulfilled", "Rejected"]


class ServiceError(Exception):
    """Raise this anywhere to stop and send a clean JSON error to the frontend."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------- JSON responses ----------
def success(message, data=None, status_code=200):
    return jsonify({"success": True, "message": message, "data": {} if data is None else data}), status_code


def error_response(message, status_code):
    return jsonify({"success": False, "message": message}), status_code


def get_json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ServiceError("Request body must be a valid JSON object")
    return body


# ---------- Validation ----------
def normalize_blood_group(value, field="blood_group"):
    """Accepts 'o+', 'AB-', and also 'O ' (a browser turns the '+' in ?blood_group=O+ into a space)."""
    if value is None or str(value).strip() == "":
        raise ServiceError(f"{field} is required")
    text = str(value).upper()
    if text.endswith(" ") and not text.strip().endswith(("+", "-")):
        text = text.strip() + "+"
    else:
        text = text.strip()
    if text not in BLOOD_GROUPS:
        raise ServiceError(f"Invalid {field}. Allowed values: {', '.join(BLOOD_GROUPS)}")
    return text


def clean_text(value, field, max_len, required=False):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if required:
            raise ServiceError(f"{field} is required")
        return None
    text = str(value).strip()
    if len(text) > max_len:
        raise ServiceError(f"{field} must be at most {max_len} characters")
    return text


def validate_email(value):
    email = clean_text(value, "email", 100)
    if email is None:
        return None
    email = email.lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ServiceError("email is not a valid email address")
    return email


def validate_phone(value):
    phone = clean_text(value, "phone", 20)
    if phone is None:
        return None
    phone = re.sub(r"[\s\-]", "", phone)
    if not re.fullmatch(r"\+?\d{7,14}", phone):
        raise ServiceError("phone must contain 7 to 14 digits (optionally starting with +)")
    return phone


def parse_date(value, field):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ServiceError(f"{field} must be a valid date in YYYY-MM-DD format")


def parse_int(value, field, minimum=None, required=True):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if required:
            raise ServiceError(f"{field} is required")
        return None
    if isinstance(value, (bool, float)):
        raise ServiceError(f"{field} must be a whole number")
    try:
        number = int(str(value).strip())
    except ValueError:
        raise ServiceError(f"{field} must be a whole number")
    if minimum is not None and number < minimum:
        raise ServiceError(f"{field} must be at least {minimum}")
    return number


def parse_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "y")


def normalize_status(value):
    status = str(value).strip().capitalize()
    if status not in REQUEST_STATUSES:
        raise ServiceError(f"Invalid status. Allowed values: {', '.join(REQUEST_STATUSES)}")
    return status
