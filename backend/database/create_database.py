import sqlite3

conn = sqlite3.connect("sample.db")
cursor = conn.cursor()

# Drop if exists
cursor.execute("DROP TABLE IF EXISTS students")

# Create table
cursor.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    grade TEXT,
    major TEXT
)
""")

students = [
    (1, "Alice", 20, "A", "Computer Science"),
    (2, "Bob", 22, "B", "Physics"),
    (3, "Charlie", 19, "A", "Mathematics"),
    (4, "David", 21, "C", "Chemistry"),
    (5, "Eva", 23, "B", "Biology"),
    (6, "Frank", 20, "A", "Computer Science"),
    (7, "Grace", 22, "B", "Physics"),
    (8, "Helen", 21, "A", "Mathematics"),
    (9, "Ian", 24, "C", "Chemistry"),
    (10, "Jack", 20, "B", "Biology"),
    (11, "Karen", 19, "A", "Computer Science"),
    (12, "Leo", 23, "C", "Physics"),
    (13, "Mona", 21, "B", "Mathematics"),
    (14, "Nina", 22, "A", "Biology"),
    (15, "Oscar", 20, "B", "Computer Science")
]

cursor.executemany(
    "INSERT INTO students VALUES (?, ?, ?, ?, ?)",
    students
)

conn.commit()
conn.close()

print("Database created successfully with 15 students.")