from config.settings import ALLOWED_SQL

def is_safe_sql(sql):

    sql = sql.lower().strip()

    if not sql.startswith(tuple(ALLOWED_SQL)):
        return False

    forbidden = ["drop", "delete", "insert", "update", "alter"]

    for word in forbidden:
        if word in sql:
            return False

    return True