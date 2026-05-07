"""
sql_repair.py
─────────────
Schema-aware SQL repair using fuzzy matching.

When the model generates SQL with slightly wrong table or column names
(e.g. "student" instead of "students", "fname" instead of "first_name"),
this module attempts to auto-correct them by finding the closest match
in the actual schema using rapidfuzz.

Repair steps:
  1. Parse the SQL with sqlparse to identify table/column references
  2. Check each identifier against the real schema
  3. If it doesn't match, fuzzy-match it to the closest real name
  4. Substitute and return repaired SQL
"""

import re
import sqlparse
from typing import Any, Dict, Optional, List

from rapidfuzz import process, fuzz


# ─────────────────────────────────────────────────────────────────────────────
# Identifier extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_from_tables(sql: str) -> List[str]:
    """Extract table names referenced in FROM and JOIN clauses."""
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([`\"\[]?[a-zA-Z_][a-zA-Z0-9_]*[`\"\]]?)",
        re.IGNORECASE,
    )
    return [m.group(1).strip('`"[]') for m in pattern.finditer(sql)]


def _extract_select_columns(sql: str) -> List[str]:
    """Extract raw column names from the SELECT clause."""
    select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return []

    cols_raw = select_match.group(1)
    if cols_raw.strip() == "*":
        return []

    # Split on comma, strip aliases (AS ...) and table qualifiers (table.col → col)
    cols = []
    for part in cols_raw.split(","):
        part = part.strip()
        # Remove alias
        part = re.split(r"\s+AS\s+", part, flags=re.IGNORECASE)[0].strip()
        # Remove table qualifier
        if "." in part:
            part = part.split(".")[-1].strip()
        # Strip aggregate wrappers like COUNT(col)
        agg_match = re.match(r"\w+\((.+)\)", part)
        if agg_match:
            inner = agg_match.group(1).strip()
            if inner != "*":
                part = inner
        cols.append(part.strip('`"[]'))

    return [c for c in cols if c]


# ─────────────────────────────────────────────────────────────────────────────
# Fuzzy correction
# ─────────────────────────────────────────────────────────────────────────────

def _best_match(name: str, candidates: List[str], threshold: int = 70) -> Optional[str]:
    """
    Return the best fuzzy match for `name` from `candidates`.
    Returns None if the best score is below `threshold`.
    """
    if not candidates:
        return None
    result = process.extractOne(
        name, candidates, scorer=fuzz.token_set_ratio
    )
    if result and result[1] >= threshold:
        return result[0]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def repair_sql(sql: str, schema: Dict[str, Any]) -> str:
    """
    Attempt to repair a broken SQL query using the actual schema.

    Steps:
      1. Fix wrong table names (fuzzy match to real table names)
      2. Fix wrong column names (fuzzy match to columns of matched table)

    Parameters
    ----------
    sql : str
        The SQL string to repair (may have wrong identifiers).
    schema : dict
        Full or pruned schema dict from schema_loader.

    Returns
    -------
    str
        Repaired SQL (or the original if no fix was possible).
    """
    real_tables = list(schema.keys())

    # ── Step 1: Fix table names ───────────────────────────────────────────
    used_tables = _extract_from_tables(sql)
    table_mapping: Dict[str, str] = {}  # wrong → correct

    for used_table in used_tables:
        if used_table in real_tables:
            continue  # already correct
        fixed = _best_match(used_table, real_tables)
        if fixed:
            table_mapping[used_table] = fixed

    # Apply table name fixes (whole-word replacement)
    repaired = sql
    for wrong, correct in table_mapping.items():
        repaired = re.sub(
            rf"\b{re.escape(wrong)}\b", correct, repaired, flags=re.IGNORECASE
        )

    # ── Step 2: Fix column names ──────────────────────────────────────────
    # Collect all real column names across tables referenced in the query
    resolved_tables = []
    for used_table in used_tables:
        real_name = table_mapping.get(used_table, used_table)
        if real_name in schema:
            resolved_tables.append(real_name)

    if resolved_tables:
        real_columns = [
            col["name"]
            for t in resolved_tables
            for col in schema[t]["columns"]
        ]

        used_cols = _extract_select_columns(repaired)
        col_mapping: Dict[str, str] = {}

        for used_col in used_cols:
            if used_col in real_columns:
                continue
            fixed_col = _best_match(used_col, real_columns, threshold=65)
            if fixed_col:
                col_mapping[used_col] = fixed_col

        for wrong_col, correct_col in col_mapping.items():
            repaired = re.sub(
                rf"\b{re.escape(wrong_col)}\b", correct_col, repaired, flags=re.IGNORECASE
            )

    return repaired