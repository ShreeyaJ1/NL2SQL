"""
db_connector.py
───────────────
Unified SQLite database connection and introspection layer.
All database interactions in the NL2SQL pipeline go through here.

This module handles:
  - Connecting to any SQLite database file
  - Extracting the full schema (tables, columns, types, PKs, FKs)
  - Sampling values for schema enrichment
  - Safely executing SQL queries with row limits
"""

import sqlite3
import re
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def get_connection(db_path: str) -> sqlite3.Connection:
    """Create and return a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Schema Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_schema(db_path: str) -> Dict[str, Any]:
    """
    Extract the full schema from a SQLite database.

    Returns a dict structured as:
    {
        "table_name": {
            "columns": [
                {
                    "name":    str,
                    "type":    str,   # e.g. "INTEGER", "TEXT", "REAL"
                    "pk":      bool,
                    "notnull": bool,
                    "default": Any,
                }
            ],
            "foreign_keys": [
                {
                    "from_col": str,
                    "to_table": str,
                    "to_col":   str,
                }
            ],
            "sample_values": {
                "col_name": ["val1", "val2", ...]   # up to 5 non-null samples
            },
            "row_count": int,
        }
    }
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    schema: Dict[str, Any] = {}

    try:
        # Enumerate user-created tables (skip internal SQLite tables)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            # ── Column info ───────────────────────────────────────────────
            cursor.execute(f"PRAGMA table_info({table});")
            cols_raw = cursor.fetchall()

            columns = [
                {
                    "name":    col[1],
                    "type":    (col[2] or "TEXT").upper(),
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk":      bool(col[5]),
                }
                for col in cols_raw
            ]

            # ── Foreign keys ──────────────────────────────────────────────
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fk_raw = cursor.fetchall()

            foreign_keys = [
                {
                    "from_col": fk[3],
                    "to_table": fk[2],
                    "to_col":   fk[4],
                }
                for fk in fk_raw
            ]

            # ── Sample values ─────────────────────────────────────────────
            sample_values: Dict[str, List[str]] = {col["name"]: [] for col in columns}
            try:
                col_names_quoted = ", ".join(f'"{c["name"]}"' for c in columns)
                cursor.execute(f'SELECT {col_names_quoted} FROM "{table}" LIMIT 10;')
                rows = cursor.fetchall()

                for col in columns:
                    seen: List[str] = []
                    for row in rows:
                        val = row[col["name"]]
                        if val is not None and str(val) not in seen:
                            seen.append(str(val))
                        if len(seen) >= 5:
                            break
                    sample_values[col["name"]] = seen

            except Exception:
                pass  # Non-critical — schema still usable without samples

            # ── Row count ─────────────────────────────────────────────────
            row_count = 0
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                row_count = cursor.fetchone()[0]
            except Exception:
                pass

            schema[table] = {
                "columns":      columns,
                "foreign_keys": foreign_keys,
                "sample_values": sample_values,
                "row_count":    row_count,
            }

    finally:
        conn.close()

    return schema


# ─────────────────────────────────────────────────────────────────────────────
# Query Execution
# ─────────────────────────────────────────────────────────────────────────────

def execute_query(
    db_path: str,
    sql: str,
    limit: int = 500,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Execute a SQL query and return (column_names, rows).

    - Automatically appends LIMIT <limit> to SELECT queries that don't
      already have one (prevents accidentally returning millions of rows).
    - Raises sqlite3.Error on failure (caller must handle).
    """
    # Inject LIMIT for SELECT queries missing one
    sql_stripped = sql.strip().rstrip(";")
    upper = sql_stripped.upper()

    if upper.startswith("SELECT") and "LIMIT" not in upper:
        sql_to_run = f"{sql_stripped} LIMIT {limit};"
    else:
        sql_to_run = sql_stripped + ";"

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql_to_run)

        col_names: List[str] = (
            [desc[0] for desc in cursor.description]
            if cursor.description
            else []
        )
        rows: List[List[Any]] = [list(row) for row in cursor.fetchall()]

        return col_names, rows

    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def get_table_names(db_path: str) -> List[str]:
    """Return a list of all user table names in the database."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def get_column_names(db_path: str, table: str) -> List[str]:
    """Return column names for a specific table."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        return [row[1] for row in cursor.fetchall()]
    finally:
        conn.close()
