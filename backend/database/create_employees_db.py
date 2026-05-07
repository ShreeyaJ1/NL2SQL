"""
Creates a sample employees database for testing multi-condition NL queries.
Run from project root: python backend/database/create_employees_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "employees.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    dept_id   INTEGER PRIMARY KEY,
    dept_name TEXT NOT NULL
);

CREATE TABLE employees (
    emp_id     INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    age        INTEGER,
    salary     REAL,
    dept_id    INTEGER REFERENCES departments(dept_id),
    hire_date  TEXT,
    city       TEXT
);

INSERT INTO departments VALUES
  (1, 'Engineering'),
  (2, 'Marketing'),
  (3, 'HR'),
  (4, 'Finance');

INSERT INTO employees VALUES
  (1,  'Alice Johnson',   29, 72000, 1, '2021-03-15', 'New York'),
  (2,  'Bob Smith',       24, 18000, 2, '2023-06-01', 'Chicago'),
  (3,  'Carol White',     35, 95000, 1, '2019-08-20', 'San Francisco'),
  (4,  'David Brown',     22, 15000, 3, '2024-01-10', 'Austin'),
  (5,  'Eva Martinez',    31, 61000, 4, '2020-11-05', 'New York'),
  (6,  'Frank Lee',       27, 28000, 2, '2022-07-18', 'Chicago'),
  (7,  'Grace Kim',       40, 110000,1, '2017-04-30', 'San Francisco'),
  (8,  'Henry Wilson',    26, 32000, 3, '2022-09-14', 'Austin'),
  (9,  'Iris Chen',       33, 78000, 4, '2020-02-28', 'New York'),
  (10, 'Jack Taylor',     28, 25500, 1, '2023-01-20', 'Chicago'),
  (11, 'Karen Davis',     45, 130000,1, '2015-06-15', 'New York'),
  (12, 'Leo Anderson',    23, 19000, 2, '2024-03-01', 'Austin'),
  (13, 'Mia Thomas',      37, 88000, 4, '2018-10-11', 'San Francisco'),
  (14, 'Noah Jackson',    30, 55000, 3, '2021-05-22', 'Chicago'),
  (15, 'Olivia Harris',   26, 24000, 2, '2023-08-09', 'New York');
""")

conn.commit()
conn.close()
print(f"Created employees database: {DB_PATH}")
print("  Tables: employees (15 rows), departments (4 rows)")
print()
print("To use it, update backend/config/settings.py:")
print('  DB_PATH = "database/employees.db"')
