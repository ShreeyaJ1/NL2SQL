import sqlite3

def load_schema(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = ""

    for table in tables:

        table_name = table[0]

        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        column_names = [col[1] for col in columns]

        schema += f"Table {table_name}: {', '.join(column_names)}\n"

    conn.close()

    return schema