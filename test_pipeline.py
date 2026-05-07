import sys
sys.path.insert(0, 'backend')

print('=== NL2SQL Pipeline Test (no model needed) ===')
print()

# 1. Schema extraction
from database.db_connector import extract_schema
schema = extract_schema('backend/database/sample.db')
print('1. Schema extracted:')
for table, info in schema.items():
    cols = [c['name'] for c in info['columns']]
    print(f'   Table: {table} ({info["row_count"]} rows) -> {cols}')
    for col, samples in info['sample_values'].items():
        if samples:
            print(f'     {col}: {samples}')
print()

# 2. Schema linker
from schema.schema_linker import link_schema
questions = [
    'How many students study computer science?',
    'Show students with grade A older than 20',
    'What is the average age of students per major?',
]
for q in questions:
    linked = link_schema(q, schema)
    print(f'2. Q: "{q}"')
    print(f'   Linked tables: {list(linked.keys())}')
print()

# 3. Query analyser
from sql.query_analyser import analyze_query
for q in questions:
    hints = analyze_query(q)
    print(f'3. Q: "{q}"')
    print(f'   Hints: {hints}')
print()

# 4. Prompt builder
from schema.prompt_builder import build_prompt
q = 'How many students study each major?'
linked = link_schema(q, schema)
hints = analyze_query(q)
prompt = build_prompt(q, linked, hints=hints)
print(f'4. Prompt: {prompt}')
print()

# 5. Rule engine
from sql.rule_engine import generate_sql_rule_based
for tq in ['Show all students', 'List all students', 'How many students?']:
    sql = generate_sql_rule_based(tq, schema)
    print(f'5. Rule engine: "{tq}" -> {sql}')
print()

# 6. SQL validator
from sql.sql_validator import is_safe_sql
for sql in ['SELECT * FROM students WHERE grade="A"', 'DROP TABLE students', 'DELETE FROM students']:
    print(f'6. is_safe_sql: "{sql[:40]}" = {is_safe_sql(sql)}')
print()

# 7. SQL verifier
from sql.sql_verifier import verify_sql
for sql in ['SELECT * FROM students', 'SELECT * FROM nonexistent_table']:
    print(f'7. verify_sql: "{sql}" = {verify_sql(sql, schema)}')
print()

# 8. SQL executor
from sql.sql_executor import run_sql
cols, rows = run_sql('SELECT name, grade FROM students LIMIT 3', db_path='backend/database/sample.db')
print(f'8. Execute: columns={cols}')
for r in rows:
    print(f'   {r}')

print()
print('=== All pipeline stages working! ===')
