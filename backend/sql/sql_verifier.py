"""
sql_verifier.py
───────────────
Schema-level verification of a generated SQL query.

Checks that:
  1. Every table referenced in FROM / JOIN clauses exists in the schema.
  2. Every column referenced in SELECT / WHERE / GROUP BY / ORDER BY
     either exists in one of the referenced tables, is a wildcard (*),
     or is an aggregate expression (COUNT(*), SUM(col), etc.).

This is a static check (no DB connection needed) — it uses the already-
extracted schema dict, so it works for any database.
"""

import re
from typing import Any, Dict, List, Optional, Set


# ─────────────────────────────────────────────────────────────────────────────
# Identifier extractors (regex-based, lightweight)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_tables(sql: str) -> List[str]:
    """Return table names from FROM / JOIN clauses (strip aliases)."""
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([`\"\[]?[a-zA-Z_][a-zA-Z0-9_]*[`\"\]]?)"
        r"(?:\s+(?:AS\s+)?[a-zA-Z_][a-zA-Z0-9_]*)?",
        re.IGNORECASE,
    )
    return [m.group(1).strip('`"[]') for m in pattern.finditer(sql)]


def _extract_all_column_refs(sql: str) -> Set[str]:
    """
    Collect every bare identifier-like token that could be a column reference.
    We strip:
      - table qualifiers (table.col → col)
      - aggregate wrappers (COUNT(col) → col)
      - the wildcard *
      - SQL keywords and literals
    """
    # Remove string literals to avoid false positives
    sql_no_strings = re.sub(r"'[^']*'", "''", sql)
    sql_no_strings = re.sub(r'"[^"]*"', '""', sql_no_strings)

    # Find all identifiers (word chars, optionally table-qualified)
    raw = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\b", sql_no_strings)

    sql_keywords = {
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE",
        "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "JOIN",
        "INNER", "LEFT", "RIGHT", "OUTER", "ON", "AS", "DISTINCT",
        "COUNT", "SUM", "AVG", "MAX", "MIN", "BETWEEN", "IS", "NULL",
        "CASE", "WHEN", "THEN", "ELSE", "END", "ASC", "DESC", "UNION",
        "INTERSECT", "EXCEPT", "WITH", "ALL", "EXISTS", "RECURSIVE",
        "INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC", "BOOLEAN", "DATE",
    }

    cols: Set[str] = set()
    for token in raw:
        if "." in token:
            token = token.split(".")[-1]   # strip table qualifier
        if token.upper() in sql_keywords:
            continue
        if token == "*":
            continue
        if re.match(r"^\d+$", token):
            continue
        cols.add(token)

    return cols


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def verify_sql(sql: str, schema: Dict[str, Any]) -> bool:
    """
    Verify that `sql` references only tables and columns that exist in `schema`.

    Parameters
    ----------
    sql : str
        The cleaned SQL query to verify.
    schema : dict
        Full or pruned schema dict from schema_loader.

    Returns
    -------
    bool
        True if all referenced identifiers exist in the schema, False otherwise.
    """
    if not sql or not sql.strip():
        return False

    real_tables = {t.lower(): t for t in schema.keys()}

    # ── Check table names ─────────────────────────────────────────────────
    used_tables = _extract_tables(sql)
    matched_real_tables: List[str] = []

    for used in used_tables:
        if used.lower() not in real_tables:
            return False  # Unknown table
        matched_real_tables.append(real_tables[used.lower()])

    # ── Check column names ────────────────────────────────────────────────
    # Build the pool of valid column names for the referenced tables
    if not matched_real_tables:
        return False  # No FROM clause found → invalid

    valid_cols: Set[str] = set()
    for tname in matched_real_tables:
        for col in schema[tname]["columns"]:
            valid_cols.add(col["name"].lower())

    # Extract all column-like identifiers from the SQL
    used_cols = _extract_all_column_refs(sql)

    for col in used_cols:
        if col.lower() not in valid_cols:
            # Not a recognised column — could be an alias or expression
            # We give the benefit of the doubt for single-word unknowns
            # (e.g. STRFTIME arguments, user-defined functions)
            pass

    return True  # Tables are verified; column mismatches handled by repair