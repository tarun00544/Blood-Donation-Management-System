import database
import json

def run_backup():
    conn = database.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SHOW TABLES")
    tables = [list(r.values())[0] for r in cur.fetchall()]
    sql_lines = ["-- BACKUP CREATED BEFORE MIGRATION", "USE blood_donation_system;"]
    for t in tables:
        cur.execute(f"SHOW CREATE TABLE `{t}`")
        create_stmt = cur.fetchone()["Create Table"]
        sql_lines.append(f"\n-- Table structure for `{t}`")
        sql_lines.append(create_stmt + ";")
        cur.execute(f"SELECT * FROM `{t}`")
        rows = cur.fetchall()
        if rows:
            sql_lines.append(f"-- Data for `{t}`")
            for r in rows:
                cols = ", ".join([f"`{k}`" for k in r.keys()])
                vals = []
                for v in r.values():
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
                        vals.append(f"'{escaped}'")
                vals_str = ", ".join(vals)
                sql_lines.append(f"INSERT INTO `{t}` ({cols}) VALUES ({vals_str});")
    conn.close()
    with open("sql/backup_before_migration.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))
    print("Database backup completed successfully to sql/backup_before_migration.sql")

if __name__ == "__main__":
    run_backup()
