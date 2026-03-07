def repair_sql(sql):

    # Fix common column mistakes
    replacements = {
        "student_name": "name",
        "student_age": "age",
        "student_grade": "grade"
    }

    for wrong, correct in replacements.items():
        sql = sql.replace(wrong, correct)

    return sql