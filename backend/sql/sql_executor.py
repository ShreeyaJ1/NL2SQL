import sqlite3

def execute_sql(db_path, sql):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(sql)

    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    conn.close()

    results = []

    for row in rows:
        results.append(dict(zip(columns, row)))

    return results