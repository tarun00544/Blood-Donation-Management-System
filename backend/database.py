"""Database layer.

* get_connection()  - opens a MySQL connection (with a friendly error if MySQL is down)
* db_cursor()       - the ONLY way the rest of the project talks to MySQL
* init_db()         - creates the database and all tables automatically
"""
import logging
import os
import re
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from config import Config
from utils import ServiceError

log = logging.getLogger(__name__)

SCHEMA_FILE = os.path.join(Config.BASE_DIR, "sql", "schema.sql")
SAMPLE_FILE = os.path.join(Config.BASE_DIR, "sql", "sample_data.sql")


def _connect(use_database=True):
    settings = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "charset": "utf8mb4",
        "connection_timeout": 10,
    }
    if use_database:
        settings["database"] = Config.DB_NAME
    return mysql.connector.connect(**settings)


def get_connection():
    try:
        return _connect()
    except Error as exc:
        log.error("MySQL connection failed: %s", exc)
        raise ServiceError(
            "Could not connect to the database. Check that MySQL is running and the DB_* values in .env are correct.",
            500,
        ) from exc


@contextmanager
def db_cursor(commit=False):
    """Usage:
        with db_cursor() as cur:                 # read-only queries
            cur.execute("SELECT ...", (value,))
        with db_cursor(commit=True) as cur:      # a TRANSACTION
            cur.execute("UPDATE ...")
            cur.execute("UPDATE ...")
    With commit=True everything is saved together when the block finishes,
    and EVERYTHING is rolled back if any error is raised inside the block.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Error:
            pass
        raise
    finally:
        cur.close()
        conn.close()


def ensure_exists(cur, table, column, value, label):
    """Raise a clean error if a referenced row (e.g. a hospital) does not exist.
    `table` and `column` are always fixed names written in our own code, never user input."""
    cur.execute(f"SELECT 1 FROM {table} WHERE {column} = %s", (value,))
    if cur.fetchone() is None:
        raise ServiceError(f"{label} with id {value} does not exist")


# ---------- Schema / sample data loading ----------
def _read_statements(path):
    with open(path, encoding="utf-8") as handle:
        lines = [ln for ln in handle.read().splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def run_sql_file(path):
    """Runs every statement of a .sql file. CREATE DATABASE / USE lines are skipped because
    init_db() already created the database named in .env and we are connected to it."""
    conn = _connect()
    cur = conn.cursor()
    try:
        for statement in _read_statements(path):
            head = statement.upper()
            if head.startswith("CREATE DATABASE") or head.startswith("USE "):
                continue
            cur.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    """Create the database (if missing) and all tables (if missing)."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", Config.DB_NAME):
        raise ValueError("DB_NAME may only contain letters, numbers and underscores")
    conn = _connect(use_database=False)
    cur = conn.cursor()
    try:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    run_sql_file(SCHEMA_FILE)


def load_sample_data():
    """Loads sql/sample_data.sql only when the hospital table is empty. Returns True if loaded."""
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM hospital")
        if cur.fetchone()["c"] > 0:
            return False
    run_sql_file(SAMPLE_FILE)
    return True
