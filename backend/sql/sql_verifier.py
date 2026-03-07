import sqlite3
import re


def verify_sql(db_path, sql):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    # find table used in query
    table_match = re.search(r"from\s+(\w+)", sql, re.IGNORECASE)

    if not table_match:
        conn.close()
        return False

    table = table_match.group(1)

    if table not in tables:
        conn.close()
        return False

    # get columns
    cursor.execute(f"PRAGMA table_info({table});")
    columns = [c[1] for c in cursor.fetchall()]

    conn.close()

    # find columns used in query
    column_matches = re.findall(r"select\s+(.*?)\s+from", sql, re.IGNORECASE)

    if column_matches:

        cols = column_matches[0].split(",")

        for col in cols:

            col = col.strip()

            if col == "*":
                continue

            if col not in columns:
                return False

    return True