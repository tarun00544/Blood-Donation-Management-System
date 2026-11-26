"""Business logic for blood requests, including the transactional 'issue blood' operation."""
from database import db_cursor, ensure_exists
from utils import (ServiceError, normalize_blood_group, normalize_status, parse_int)

REQUEST_SELECT = """
SELECT r.request_id, r.recipient_id, rec.name AS recipient_name, r.blood_group, r.units_required,
       r.hospital_id, h.name AS hospital_name, r.request_date, r.status
FROM blood_request r
LEFT JOIN recipient rec ON rec.recipient_id = r.recipient_id
LEFT JOIN hospital h ON h.hospital_id = r.hospital_id
"""


def _fetch(cur, request_id):
    cur.execute(REQUEST_SELECT + " WHERE r.request_id = %s", (request_id,))
    row = cur.fetchone()
    if row is None:
        raise ServiceError("Blood request not found", 404)
    return row


def _validate(cur, data):
    clean = {
        "recipient_id": parse_int(data.get("recipient_id"), "recipient_id", minimum=1),
        "blood_group": normalize_blood_group(data.get("blood_group")),
        "units_required": parse_int(data.get("units_required"), "units_required", minimum=1),
        "hospital_id": parse_int(data.get("hospital_id"), "hospital_id", minimum=1),
        "status": normalize_status(data.get("status") or "Pending"),
    }
    ensure_exists(cur, "recipient", "recipient_id", clean["recipient_id"], "Recipient")
    ensure_exists(cur, "hospital", "hospital_id", clean["hospital_id"], "Hospital")
    if clean["status"] == "Fulfilled":
        raise ServiceError("A request becomes 'Fulfilled' only by issuing blood "
                           "(POST /api/blood-requests/<id>/issue), so stock stays correct")
    return clean


def list_requests(args):
    where, params = [], []
    if args.get("status"):
        where.append("r.status = %s")
        params.append(normalize_status(args.get("status")))
    if args.get("blood_group"):
        where.append("r.blood_group = %s")
        params.append(normalize_blood_group(args.get("blood_group")))
    if args.get("hospital_id"):
        where.append("r.hospital_id = %s")
        params.append(parse_int(args.get("hospital_id"), "hospital_id", minimum=1))
    if args.get("recipient_id"):
        where.append("r.recipient_id = %s")
        params.append(parse_int(args.get("recipient_id"), "recipient_id", minimum=1))
    sql = REQUEST_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.request_date DESC, r.request_id DESC"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def get_request(request_id):
    with db_cursor() as cur:
        return _fetch(cur, request_id)


def create_request(body):
    recipient_id = parse_int(body.get("recipient_id"), "recipient_id", minimum=1)
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT blood_group, required_units, hospital_id FROM recipient WHERE recipient_id = %s",
                    (recipient_id,))
        recipient = cur.fetchone()
        if recipient is None:
            raise ServiceError(f"Recipient with id {recipient_id} does not exist")
        # Anything the frontend does not send is taken from the recipient record.
        data = {"recipient_id": recipient_id, "blood_group": recipient["blood_group"],
                "units_required": recipient["required_units"], "hospital_id": recipient["hospital_id"],
                "status": "Pending"}
        data.update({k: v for k, v in body.items() if k in data and v not in (None, "")})
        clean = _validate(cur, data)
        cur.execute(
            "INSERT INTO blood_request (recipient_id, blood_group, units_required, hospital_id, status) "
            "VALUES (%s, %s, %s, %s, %s)",
            (clean["recipient_id"], clean["blood_group"], clean["units_required"],
             clean["hospital_id"], clean["status"]),
        )
        return _fetch(cur, cur.lastrowid)


def update_request(request_id, body):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT recipient_id, blood_group, units_required, hospital_id, status "
                    "FROM blood_request WHERE request_id = %s FOR UPDATE", (request_id,))
        existing = cur.fetchone()
        if existing is None:
            raise ServiceError("Blood request not found", 404)
        if existing["status"] == "Fulfilled":
            raise ServiceError("A fulfilled request cannot be modified")
        clean = _validate(cur, {**existing, **body})
        cur.execute(
            "UPDATE blood_request SET recipient_id=%s, blood_group=%s, units_required=%s, hospital_id=%s, "
            "status=%s WHERE request_id=%s",
            (clean["recipient_id"], clean["blood_group"], clean["units_required"],
             clean["hospital_id"], clean["status"], request_id),
        )
        return _fetch(cur, request_id)


def delete_request(request_id):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM blood_request WHERE request_id = %s", (request_id,))
        if cur.rowcount == 0:
            raise ServiceError("Blood request not found", 404)


def issue_blood(request_id):
    """Issue blood for a request - ONE TRANSACTION:
       1. lock the request row            4. subtract units (oldest expiry first)
       2. lock the matching valid stock   5. mark the request 'Fulfilled'
       3. check there are enough units    6. COMMIT  (any error above => ROLLBACK, nothing changes)
    """
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT request_id, blood_group, units_required, hospital_id, status "
                    "FROM blood_request WHERE request_id = %s FOR UPDATE", (request_id,))
        req = cur.fetchone()
        if req is None:
            raise ServiceError("Blood request not found", 404)
        if req["status"] not in ("Pending", "Approved"):
            raise ServiceError(f"Cannot issue blood: request is already '{req['status']}'")

        needed = req["units_required"]
        # Only batches of the requested group, in the selected hospital, NOT expired. Oldest expiry first.
        cur.execute(
            "SELECT stock_id, units_available, expiry_date FROM blood_stock "
            "WHERE blood_group = %s AND hospital_id = %s AND units_available > 0 "
            "AND (expiry_date IS NULL OR expiry_date >= CURDATE()) "
            "ORDER BY expiry_date IS NULL, expiry_date ASC, stock_id ASC FOR UPDATE",
            (req["blood_group"], req["hospital_id"]),
        )
        batches = cur.fetchall()
        available = sum(b["units_available"] for b in batches)
        if available < needed:
            raise ServiceError(
                f"Insufficient stock: {needed} unit(s) of {req['blood_group']} required but only "
                f"{available} valid (non-expired) unit(s) are available at this hospital")

        remaining, used = needed, []
        for batch in batches:
            take = min(batch["units_available"], remaining)
            # "units_available >= take" makes it impossible for stock to go negative.
            cur.execute(
                "UPDATE blood_stock SET units_available = units_available - %s "
                "WHERE stock_id = %s AND units_available >= %s",
                (take, batch["stock_id"], take),
            )
            if cur.rowcount != 1:
                raise ServiceError("Stock changed while issuing blood. Please try again")
            used.append({"stock_id": batch["stock_id"], "units_taken": take, "expiry_date": batch["expiry_date"]})
            remaining -= take
            if remaining == 0:
                break

        cur.execute("UPDATE blood_request SET status = 'Fulfilled' WHERE request_id = %s", (request_id,))
        result = _fetch(cur, request_id)
        result["units_issued"] = needed
        result["stock_batches_used"] = used
        return result
