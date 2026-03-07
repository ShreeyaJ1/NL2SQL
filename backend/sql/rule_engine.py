import re

def generate_sql_rule_based(question):

    q = question.lower()

    # ------------------------
    # BLOCK COMPLEX QUERIES
    # ------------------------

    complex_words = [
        "average",
        "avg",
        "sum",
        "group",
        "per",
        "minimum",
        "maximum",
        "oldest",
        "youngest",
        "count",
        "number of"
    ]

    for word in complex_words:
        if word in q:
            return None


    # ------------------------
    # SELECT COLUMNS
    # ------------------------

    columns = []

    if "name" in q:
        columns.append("name")

    if "age" in q:
        columns.append("age")

    if "major" in q:
        columns.append("major")

    if not columns:
        columns = ["*"]

    select_clause = ", ".join(columns)


    # ------------------------
    # CONDITIONS
    # ------------------------

    conditions = []

    grade_match = re.search(r"grade\s*(=|is)?\s*([abc])", q)
    if grade_match:
        grade = grade_match.group(2).upper()
        conditions.append(f"grade = '{grade}'")

    age_match = re.search(r"age\s*(=|is)?\s*(\d+)", q)
    if age_match:
        age = age_match.group(2)
        conditions.append(f"age = {age}")

    if "older than" in q:
        age_match = re.search(r"older than\s*(\d+)", q)
        if age_match:
            conditions.append(f"age > {age_match.group(1)}")

    majors = ["physics", "biology", "mathematics", "computer science", "chemistry"]

    for m in majors:
        if m in q:
            conditions.append(f"LOWER(major) = LOWER('{m}')")


    # ------------------------
    # BUILD SQL
    # ------------------------

    sql = f"SELECT {select_clause} FROM students"

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    return sql