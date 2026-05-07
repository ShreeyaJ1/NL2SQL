"""
response_formatter.py
─────────────────────
Formats query results into a rich, consistent JSON structure.
"""

from typing import Any, Dict, List, Optional


def format_success(
    question:   str,
    sql:        str,
    columns:    List[str],
    rows:       List[List[Any]],
    source:     str = "model",   # "model" | "rule_engine"
    row_count:  Optional[int] = None,
) -> Dict[str, Any]:
    """
    Format a successful NL2SQL execution result.

    Parameters
    ----------
    question : str
        Original natural language question.
    sql : str
        The generated (and possibly repaired) SQL query.
    columns : list[str]
        Column names from the query result.
    rows : list[list]
        Result rows.
    source : str
        Which component generated the SQL.
    row_count : int, optional
        Total rows in result (may differ from len(rows) if limited).

    Returns
    -------
    dict
    """
    # Convert any non-serialisable values to strings
    safe_rows = [
        [_safe(v) for v in row]
        for row in rows
    ]

    return {
        "success":      True,
        "question":     question,
        "sql":          sql,
        "source":       source,
        "columns":      columns,
        "rows":         safe_rows,
        "row_count":    row_count if row_count is not None else len(rows),
    }


def format_error(
    question: str,
    message:  str,
    sql:      Optional[str] = None,
    stage:    Optional[str] = None,
) -> Dict[str, Any]:
    """
    Format a failure response.

    Parameters
    ----------
    question : str
        Original natural language question.
    message : str
        Human-readable error description.
    sql : str, optional
        The SQL that caused the failure (for debugging).
    stage : str, optional
        Pipeline stage where the failure occurred.
    """
    result: Dict[str, Any] = {
        "success":  False,
        "question": question,
        "message":  message,
    }
    if sql:
        result["sql"] = sql
    if stage:
        result["stage"] = stage
    return result


def _safe(value: Any) -> Any:
    """Convert non-JSON-serialisable types to safe equivalents."""
    if value is None:
        return None
    if isinstance(value, (int, float, bool, str)):
        return value
    return str(value)