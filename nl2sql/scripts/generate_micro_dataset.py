import random
import json

schema = "Schema: Table students: id, name, age, grade, major."

majors = [
    "Physics",
    "Biology",
    "Mathematics",
    "Chemistry",
    "Computer Science",
    "Economics",
    "Statistics"
]

grades = ["A", "B", "C"]
ages = list(range(18, 26))

question_templates = [
    "List all students",
    "Show all students",
    "Show student names",
    "Show student ages",
    "Show student majors",
]

data = []

# Basic queries
for q in question_templates:

    if "names" in q:
        sql = "SELECT name FROM students"
    elif "ages" in q:
        sql = "SELECT age FROM students"
    elif "majors" in q:
        sql = "SELECT major FROM students"
    else:
        sql = "SELECT * FROM students"

    data.append({
        "input": f"{schema} Question: {q}",
        "target": sql
    })


# Grade queries
for g in grades:

    data.append({
        "input": f"{schema} Question: Show students with grade {g}",
        "target": f"SELECT * FROM students WHERE grade='{g}'"
    })

    data.append({
        "input": f"{schema} Question: Show names of students with grade {g}",
        "target": f"SELECT name FROM students WHERE grade='{g}'"
    })


# Major queries
for m in majors:

    data.append({
        "input": f"{schema} Question: Show students studying {m}",
        "target": f"SELECT * FROM students WHERE major='{m}'"
    })

    data.append({
        "input": f"{schema} Question: Show names of students studying {m}",
        "target": f"SELECT name FROM students WHERE major='{m}'"
    })

    data.append({
        "input": f"{schema} Question: Show ages of students studying {m}",
        "target": f"SELECT age FROM students WHERE major='{m}'"
    })


# Age queries
for age in ages:

    data.append({
        "input": f"{schema} Question: Show students with age {age}",
        "target": f"SELECT * FROM students WHERE age={age}"
    })

    data.append({
        "input": f"{schema} Question: Show names of students with age {age}",
        "target": f"SELECT name FROM students WHERE age={age}"
    })


# Combined conditions
for age in ages:
    for g in grades:

        data.append({
            "input": f"{schema} Question: Show students older than {age} with grade {g}",
            "target": f"SELECT * FROM students WHERE age>{age} AND grade='{g}'"
        })


# Major + grade
for m in majors:
    for g in grades:

        data.append({
            "input": f"{schema} Question: Show students studying {m} with grade {g}",
            "target": f"SELECT * FROM students WHERE major='{m}' AND grade='{g}'"
        })


random.shuffle(data)

# Ensure enough samples
while len(data) < 300:
    data.append(random.choice(data))

random.shuffle(data)

split = int(len(data) * 0.8)

train = data[:split]
eval = data[split:]


with open("../models/micro_train.jsonl", "w") as f:
    for ex in train:
        f.write(json.dumps(ex) + "\n")

with open("../models/micro_eval.jsonl", "w") as f:
    for ex in eval:
        f.write(json.dumps(ex) + "\n")

print("Generated dataset")
print("Train examples:", len(train))
print("Eval examples:", len(eval))