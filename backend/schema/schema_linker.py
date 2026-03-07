def link_schema(question, schema):

    q = question.lower()

    columns = [
        "id",
        "name",
        "age",
        "grade",
        "major"
    ]

    mentioned = []

    for col in columns:
        if col in q:
            mentioned.append(col)

    if mentioned:

        linked = "Relevant columns: " + ", ".join(mentioned)

        return schema + "\n" + linked

    return schema