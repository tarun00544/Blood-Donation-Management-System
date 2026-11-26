"""Business logic for blood stock (inventory). Every write runs inside a transaction."""
from config import Config
from database import db_cursor, ensure_exists
from utils import (BLOOD_GROUPS, ServiceError, normalize_blood_group, parse_date, parse_int)

# Config.EXPIRING_SOON_DAYS is an int read from .env (never user input), so it is safe in the SQL text.
STOCK_SELECT = """
SELECT s.stock_id, s.blood_group, s.units_available, s.expiry_date, s.hospital_id,
       h.name AS hospital_name,
       CASE WHEN s.expiry_date IS NOT NULL AND s.expiry_date < CURDATE() THEN 'Expired'
            WHEN s.expiry_date IS NOT NULL
                 AND s.expiry_date <= DATE_ADD(CURDATE(), INTERVAL {soon} DAY) THEN 'Expiring Soon'
            ELSE 'Valid' END AS expiry_status
FROM blood_stock s
LEFT JOIN hospital h ON h.hospital_id = s.hospital_id
""".format(soon=int(Config.EXPIRING_SOON_DAYS))

VALID_SQL = "(expiry_date IS NULL OR expiry_date >= CURDATE())"


def _validate(cur, data):
    clean = {
        "blood_group": normalize_blood_group(data.get("blood_group")),
        "units_available": parse_int(data.get("units_available"), "units_available", minimum=0),
        "expiry_date": parse_date(data.get("expiry_date"), "expiry_date"),
        "hospital_id": parse_int(data.get("hospital_id"), "hospital_id", minimum=1),
    }
    ensure_exists(cur, "hospital", "hospital_id", clean["hospital_id"], "Hospital")
    return clean


def _fetch(cur, stock_id):
    cur.execute(STOCK_SELECT + " WHERE s.stock_id = %s", (stock_id,))
    row = cur.fetchone()
    if row is None:
        raise ServiceError("Blood stock record not found", 404)
    return row


def list_stock(args):
    where, params = [], []
    if args.get("blood_group"):
        where.append("s.blood_group = %s")
        params.append(normalize_blood_group(args.get("blood_group")))
    if args.get("hospital_id"):
        where.append("s.hospital_id = %s")
        params.append(parse_int(args.get("hospital_id"), "hospital_id", minimum=1))
    expiry = (args.get("expiry") or "").strip().lower().replace("-", "_")
    if expiry:
        if expiry == "expired":
            where.append("(s.expiry_date IS NOT NULL AND s.expiry_date < CURDATE())")
        elif expiry == "valid":
            where.append("(s.expiry_date IS NULL OR s.expiry_date >= CURDATE())")
        elif expiry == "expiring_soon":
            where.append("(s.expiry_date >= CURDATE() AND s.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY))")
            params.append(Config.EXPIRING_SOON_DAYS)
        else:
            raise ServiceError("Invalid expiry filter. Allowed values: expired, valid, expiring_soon")
    sql = STOCK_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.stock_id"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def get_stock(stock_id):
    with db_cursor() as cur:
        return _fetch(cur, stock_id)


def create_stock(body):
    """Adds a batch. If the SAME blood group + hospital + expiry date already exists, the units are
    added to that batch instead of creating a duplicate row. Returns (row, merged_flag)."""
    with db_cursor(commit=True) as cur:
        clean = _validate(cur, body)
        cur.execute(
            "SELECT stock_id FROM blood_stock "
            "WHERE blood_group = %s AND hospital_id = %s AND expiry_date <=> %s FOR UPDATE",
            (clean["blood_group"], clean["hospital_id"], clean["expiry_date"]),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE blood_stock SET units_available = units_available + %s WHERE stock_id = %s",
                        (clean["units_available"], existing["stock_id"]))
            return _fetch(cur, existing["stock_id"]), True
        cur.execute(
            "INSERT INTO blood_stock (blood_group, units_available, expiry_date, hospital_id) VALUES (%s,%s,%s,%s)",
            (clean["blood_group"], clean["units_available"], clean["expiry_date"], clean["hospital_id"]),
        )
        return _fetch(cur, cur.lastrowid), False


def update_stock(stock_id, body):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT blood_group, units_available, expiry_date, hospital_id "
                    "FROM blood_stock WHERE stock_id = %s FOR UPDATE", (stock_id,))
        existing = cur.fetchone()
        if existing is None:
            raise ServiceError("Blood stock record not found", 404)
        clean = _validate(cur, {**existing, **body})
        cur.execute(
            "UPDATE blood_stock SET blood_group=%s, units_available=%s, expiry_date=%s, hospital_id=%s "
            "WHERE stock_id=%s",
            (clean["blood_group"], clean["units_available"], clean["expiry_date"], clean["hospital_id"], stock_id),
        )
        return _fetch(cur, stock_id)


def delete_stock(stock_id):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM blood_stock WHERE stock_id = %s", (stock_id,))
        if cur.rowcount == 0:
            raise ServiceError("Blood stock record not found", 404)


# ---------- helpers used by dashboard and reports ----------
def inventory_by_group(cur):
    """Valid (non-expired) and expired units for ALL 8 blood groups (0 when none)."""
    cur.execute(f"""
        SELECT blood_group,
               COALESCE(SUM(CASE WHEN {VALID_SQL} THEN units_available END), 0) AS units_available,
               COALESCE(SUM(CASE WHEN expiry_date < CURDATE() THEN units_available END), 0) AS expired_units
        FROM blood_stock GROUP BY blood_group""")
    found = {r["blood_group"]: r for r in cur.fetchall()}
    return [
        {"blood_group": g,
         "units_available": int(found[g]["units_available"]) if g in found else 0,
         "expired_units": int(found[g]["expired_units"]) if g in found else 0}
        for g in BLOOD_GROUPS
    ]


def low_stock_groups(inventory):
    return [{"blood_group": i["blood_group"], "units_available": i["units_available"]}
            for i in inventory if i["units_available"] < Config.LOW_STOCK_THRESHOLD]
