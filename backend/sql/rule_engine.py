"""
rule_engine.py
──────────────
Lightweight generic rule-based fallback for trivially simple queries.

Unlike the old version, this engine has ZERO hardcoded table names,
column names, or domain-specific logic. It only handles the single
universal case: "list / show / get everything from a table" where
the table name is mentioned explicitly in the question.

For all other queries, it returns None and defers to the model.
"""

import re
from typing import Any, Dict, Optional


# Trigger phrases for "show everything" queries
_SHOW_ALL_PATTERNS = [
    r"\bshow\s+all\b",
    r"\blist\s+all\b",
    r"\bget\s+all\b",
    r"\bdisplay\s+all\b",
    r"\bfetch\s+all\b",
    r"\bsee\s+all\b",
    r"\bview\s+all\b",
    r"\bshow\s+everything\b",
    r"\blist\s+everything\b",
]

_SHOW_ALL_RE = re.compile("|".join(_SHOW_ALL_PATTERNS), re.IGNORECASE)


def generate_sql_rule_based(
    question: str,
    schema: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Try to handle the question with a simple rule — return None if unsure.

    Currently handles only:
      "Show all [table_name]" / "List all [table_name]" / "Get all [table_name]"
    → SELECT * FROM <table_name>

    Parameters
    ----------
    question : str
        The natural language question.
    schema : dict, optional
        The current schema dict. Used to verify the table exists.
        If None, skips table verification.

    Returns
    -------
    str or None
        A SQL string if a rule matched, otherwise None.
    """
    if not _SHOW_ALL_RE.search(question):
        return None

    if schema is None:
        return None

    # Try to find a table name mentioned in the question
    q_lower = question.lower()
    for table_name in schema.keys():
        # Match both exact name and a simple plural (e.g. "students" → "student")
        variants = {table_name.lower(), table_name.lower().rstrip("s")}
        for variant in variants:
            if variant in q_lower:
                return f"SELECT * FROM {table_name}"

    return None