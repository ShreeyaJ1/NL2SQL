"""
Live API test — sends NL queries to the running server and prints results.
Run: conda run -n nl2sql python test_api.py
"""
import urllib.request
import json
import sys

BASE = "http://127.0.0.1:5000"

def query(question):
    data = json.dumps({"question": question}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/query",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())
    except Exception as e:
        return {"success": False, "message": str(e)}


def show(r, q):
    print(f"\n{'-'*60}")
    print(f"  Q : {q}")
    if r.get("success"):
        print(f"  SQL    : {r['sql']}")
        print(f"  Source : {r['source']}")
        if r["columns"]:
            header = " | ".join(r["columns"])
            print(f"  Result : {header}")
            for row in r["rows"][:5]:
                print(f"           {' | '.join(str(v) for v in row)}")
        print(f"  ({r['row_count']} rows)")
    else:
        print(f"  [FAIL] {r.get('message', 'unknown error')}")
        if r.get("stage"):
            print(f"    Stage: {r['stage']}")


# Health check
print("Checking server health...")
try:
    h = json.loads(urllib.request.urlopen(f"{BASE}/api/health", timeout=5).read())
    print(f"  Model loaded : {h['model_loaded']}  ({h['model_name']})")
    print(f"  DB           : {h['db_path']}  ({h['db_tables']} tables)")
except Exception as e:
    print(f"  Server not reachable: {e}")
    sys.exit(1)

# Test queries
QUERIES = [
    # Your original question
    "show employees above age 25 with salaries over 25k",
    # More variations
    "Show all employees",
    "How many employees are in each department?",
    "Who are the top 5 highest paid employees?",
    "What is the average salary?",
    "Show employees in New York",
    "List employees hired after 2022",
    "Show employees with salary between 50000 and 100000",
]

for q in QUERIES:
    r = query(q)
    show(r, q)

print(f"\n{'='*60}")
print("Test complete.")
