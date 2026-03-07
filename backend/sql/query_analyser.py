import re


def analyze_query(question):

    q = question.lower()

    hints = {}

    # Columns requested
    columns = []

    if "name" in q:
        columns.append("name")

    if "age" in q or "ages" in q:
        columns.append("age")

    if "major" in q or "majors" in q:
        columns.append("major")

    if columns:
        hints["columns"] = columns

    # Grade filter
    grade_match = re.search(r"grade\s*(=|is)?\s*([abc])", q)
    if grade_match:
        hints["grade"] = grade_match.group(2).upper()

    # Age filter
    age_match = re.search(r"age\s*(=|is|older than)?\s*(\d+)", q)
    if age_match:
        hints["age"] = age_match.group(2)

        if "older" in q:
            hints["age_operator"] = ">"

    # Major filter
    majors = ["physics", "biology", "mathematics", "computer science", "chemistry"]

    for m in majors:
        if m in q:
            hints["major"] = m

    return hints