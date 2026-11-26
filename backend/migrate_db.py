"""Migration runner for BLOODCARE.
Applies schema upgrades safely without dropping tables or losing data.
"""
import os
import mysql.connector
from werkzeug.security import generate_password_hash
import database
from config import Config

def column_exists(cur, table, column):
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (Config.DB_NAME, table, column)
    )
    return cur.fetchone()["cnt"] > 0

def foreign_key_exists(cur, table, constraint_name):
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.TABLE_CONSTRAINTS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s",
        (Config.DB_NAME, table, constraint_name)
    )
    return cur.fetchone()["cnt"] > 0

def run_migration():
    print("Starting BLOODCARE database migration...")
    database.init_db()

    # 1. Run auth_migration.sql
    migration_file = os.path.join(Config.BASE_DIR, "sql", "auth_migration.sql")
    database.run_sql_file(migration_file)
    print("Users table and default admin verified.")

    # 2. Add columns to donor table
    with database.db_cursor(commit=True) as cur:
        if not column_exists(cur, "donor", "user_id"):
            print("Adding user_id to donor table...")
            cur.execute("ALTER TABLE donor ADD COLUMN user_id INT NULL")
        
        if not column_exists(cur, "donor", "age"):
            print("Adding age to donor table...")
            cur.execute("ALTER TABLE donor ADD COLUMN age INT NULL")

        if not column_exists(cur, "donor", "is_available"):
            print("Adding is_available to donor table...")
            cur.execute("ALTER TABLE donor ADD COLUMN is_available BOOLEAN NOT NULL DEFAULT TRUE")

        if not foreign_key_exists(cur, "donor", "fk_donor_user"):
            print("Adding fk_donor_user constraint...")
            cur.execute(
                "ALTER TABLE donor ADD CONSTRAINT fk_donor_user "
                "FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE CASCADE"
            )

    # 3. Add columns to blood_request table
    with database.db_cursor(commit=True) as cur:
        if not column_exists(cur, "blood_request", "user_id"):
            print("Adding user_id to blood_request table...")
            cur.execute("ALTER TABLE blood_request ADD COLUMN user_id INT NULL")

        if not column_exists(cur, "blood_request", "required_date"):
            print("Adding required_date to blood_request table...")
            cur.execute("ALTER TABLE blood_request ADD COLUMN required_date DATE NULL")

        if not column_exists(cur, "blood_request", "notes"):
            print("Adding notes to blood_request table...")
            cur.execute("ALTER TABLE blood_request ADD COLUMN notes TEXT NULL")

        if not foreign_key_exists(cur, "blood_request", "fk_request_user"):
            print("Adding fk_request_user constraint...")
            cur.execute(
                "ALTER TABLE blood_request ADD CONSTRAINT fk_request_user "
                "FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE CASCADE"
            )

    # 4. Check if demo donors or hospitals are missing; populate if needed
    with database.db_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) AS c FROM donor")
        if cur.fetchone()["c"] <= 1:
            print("Populating diverse demo donors...")
            from datetime import date, timedelta
            donors = [
                ('Rahul Sharma',   'O+',  '9876500001', 'rahul.sharma@example.com',  'Ludhiana',   120),
                ('Priya Singh',    'A+',  '9876500002', 'priya.singh@example.com',   'Amritsar',   200),
                ('Amandeep Kaur',  'B+',  '9876500003', 'amandeep.kaur@example.com', 'Chandigarh', None),
                ('Vikram Malhotra','AB+', '9876500004', 'vikram.m@example.com',      'Jalandhar',  30),
                ('Neha Gupta',     'O-',  '9876500005', 'neha.gupta@example.com',    'Ludhiana',   95),
                ('Harjot Singh',   'A-',  '9876500006', 'harjot.singh@example.com',  'Patiala',    150),
                ('Simran Arora',   'B-',  '9876500007', 'simran.arora@example.com',  'Amritsar',   None),
                ('Rohit Verma',    'O+',  '9876500008', 'rohit.verma@example.com',   'Chandigarh', 60),
                ('Kiran Bedi',     'AB-', '9876500009', 'kiran.bedi@example.com',    'Jalandhar',  300),
                ('Manpreet Gill',  'A+',  '9876500010', 'manpreet.gill@example.com', 'Ludhiana',   100),
                ('Pooja Mehta',    'B+',  '9876500011', 'pooja.mehta@example.com',   'Patiala',    45),
                ('Arjun Thakur',   'O+',  '9876500012', 'arjun.thakur@example.com',  'Amritsar',   180)
            ]
            for name, bg, phone, email, loc, days in donors:
                cur.execute('SELECT 1 FROM donor WHERE email = %s OR phone = %s', (email, phone))
                if not cur.fetchone():
                    dt = (date.today() - timedelta(days=days)) if days else None
                    cur.execute(
                        'INSERT INTO donor (name, blood_group, phone, email, location, last_donation_date, is_available) VALUES (%s, %s, %s, %s, %s, %s, TRUE)',
                        (name, bg, phone, email, loc, dt)
                    )

    with database.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM hospital")
        hosp_count = cur.fetchone()["c"]
    
    if hosp_count == 0:
        print("Hospital table is empty, loading demo hospitals and blood stock...")
        # Run sample data statements safely
        sample_file = os.path.join(Config.BASE_DIR, "sql", "sample_data.sql")
        conn = database._connect()
        cur = conn.cursor()
        try:
            for stmt in database._read_statements(sample_file):
                head = stmt.upper()
                if head.startswith("CREATE DATABASE") or head.startswith("USE "):
                    continue
                try:
                    cur.execute(stmt)
                except mysql.connector.Error as err:
                    # Ignore duplicate key error on existing donor
                    if err.errno == 1062:
                        continue
                    raise
            conn.commit()
            print("Sample data populated successfully.")
        finally:
            cur.close()
            conn.close()

    # 5. Create default demo regular user: user@bloodcare.com / User@123
    with database.db_cursor(commit=True) as cur:
        cur.execute("SELECT user_id FROM users WHERE email = %s", ("user@bloodcare.com",))
        if not cur.fetchone():
            user_pw_hash = generate_password_hash("User@123")
            cur.execute(
                "INSERT INTO users (name, email, phone, password_hash, role, is_active) "
                "VALUES (%s, %s, %s, %s, 'user', TRUE)",
                ("Demo User", "user@bloodcare.com", "+919876543210", user_pw_hash)
            )
            print("Demo user created: user@bloodcare.com / User@123")

    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
