import re

def clean_sql(sql):

    sql = sql.strip()

    sql = sql.replace("\n", " ")

    sql = sql.rstrip(";")

    sql = sql.lower()

    # Fix case-insensitive comparisons
    pattern = r"(\w+)\s*=\s*'([^']+)'"

    def replace(match):
        column = match.group(1)
        value = match.group(2)
        return f"LOWER({column}) = LOWER('{value}')"

    sql = re.sub(pattern, replace, sql)

    # Fix missing SELECT *
    if sql.startswith("from students"):
        sql = "select * " + sql

    return sql