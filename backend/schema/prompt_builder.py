def build_prompt(question, schema, hints):

    hint_text = ""

    if hints:

        hint_text = "Important query hints:\n"

        if "columns" in hints:
            hint_text += f"Requested columns: {', '.join(hints['columns'])}\n"

        if "grade" in hints:
            hint_text += f"Filter grade = {hints['grade']}\n"

        if "age" in hints:
            op = hints.get("age_operator", "=")
            hint_text += f"Filter age {op} {hints['age']}\n"

        if "major" in hints:
            hint_text += f"Filter major = {hints['major']}\n"

    prompt = f"""
Convert the question to SQL.

Database Schema:
{schema}

{hint_text}

Question:
{question}

SQL query:
"""

    return prompt.strip()