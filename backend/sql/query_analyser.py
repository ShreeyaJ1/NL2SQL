"""
query_analyser.py
─────────────────
Generic NLP-based query intent extraction.

Analyses the natural language question to detect:
  - Aggregation type (COUNT, SUM, AVG, MAX, MIN)
  - Sorting intent (ORDER BY ASC/DESC)
  - Limit intent (TOP N, FIRST N)
  - Negation ("not", "except", "without")
  - Comparison operators for numeric/date filters

This information is passed to the prompt builder as optional hints
to guide the model, and is also used during SQL repair/validation.

No hardcoded table or column names — works with any database.
"""

import re
from typing import Any, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Pattern definitions
# ─────────────────────────────────────────────────────────────────────────────

# Aggregation patterns (NL phrase → SQL aggregate function)
_AGG_PATTERNS = [
    (r"\bhow many\b",                       "COUNT"),
    (r"\bcount\b",                          "COUNT"),
    (r"\bnumber of\b",                      "COUNT"),
    (r"\btotal\b",                          "SUM"),
    (r"\bsum\b",                            "SUM"),
    (r"\baverage\b|\bavg\b|\bmean\b",       "AVG"),
    (r"\bmaximum\b|\bmax\b|\bhighest\b|\blargest\b|\bmost\b",  "MAX"),
    (r"\bminimum\b|\bmin\b|\blowest\b|\bsmallest\b|\bleast\b", "MIN"),
]

# Sort direction patterns
_SORT_PATTERNS = [
    (r"\bascending\b|\basc\b|\blowest first\b|\bsmallest first\b",  "ASC"),
    (r"\bdescending\b|\bdesc\b|\bhighest first\b|\blargest first\b|\btop\b|\bmost\b", "DESC"),
    (r"\blatest\b|\brecent\b|\bnewest\b",   "DESC"),
    (r"\boldest\b|\bearliest\b",            "ASC"),
]

# LIMIT / TOP N patterns
_LIMIT_RE = re.compile(
    r"\b(?:top|first|last|limit|only)\s+(\d+)\b",
    re.IGNORECASE,
)

# Comparison patterns for numeric filters
_CMP_PATTERNS = [
    (r"\bgreater than\b|\bmore than\b|\bover\b|\babove\b|\bolder than\b",   ">"),
    (r"\bless than\b|\bunder\b|\bbelow\b|\byounger than\b|\bcheaper than\b","<"),
    (r"\bgreater than or equal\b|\bat least\b|\bno less than\b",           ">="),
    (r"\bless than or equal\b|\bat most\b|\bno more than\b",              "<="),
    (r"\bnot equal\b|\bdifferent from\b|\bexcluding\b",                   "!="),
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyze_query(question: str) -> Dict[str, Any]:
    """
    Analyse a natural language question and return a hints dictionary.

    Returns
    -------
    dict with any of the following keys (only set when detected):
        "aggregation" : str   — "COUNT" | "SUM" | "AVG" | "MAX" | "MIN"
        "sort"        : str   — "ASC" | "DESC"
        "limit"       : int   — e.g. 10 for "top 10"
        "comparison"  : str   — ">" | "<" | ">=" | "<=" | "!="
        "negation"    : bool  — True if the question contains negation
        "distinct"    : bool  — True if "unique" / "distinct" detected
        "join_likely" : bool  — True if the question implies a JOIN
    """
    q = question.lower()
    hints: Dict[str, Any] = {}

    # Aggregation
    for pattern, agg in _AGG_PATTERNS:
        if re.search(pattern, q):
            hints["aggregation"] = agg
            break  # Use the first (highest-priority) match

    # Sort direction
    for pattern, direction in _SORT_PATTERNS:
        if re.search(pattern, q):
            hints["sort"] = direction
            break

    # Limit / TOP N
    limit_match = _LIMIT_RE.search(q)
    if limit_match:
        hints["limit"] = int(limit_match.group(1))

    # Comparison operator
    for pattern, op in _CMP_PATTERNS:
        if re.search(pattern, q):
            hints["comparison"] = op
            break

    # Negation
    if re.search(r"\bnot\b|\bno\b|\bnone\b|\bexcept\b|\bwithout\b|\bexclude\b", q):
        hints["negation"] = True

    # DISTINCT
    if re.search(r"\bunique\b|\bdistinct\b|\bdifferent\b", q):
        hints["distinct"] = True

    # JOIN likelihood — if question references multiple concepts that could
    # belong to different tables. We check for common linking words.
    if re.search(
        r"\bwho\b.+\bfrom\b|\bjoin\b|\brelated\b|\bbelongs?\b|\bwith their\b|\balong with\b",
        q,
    ):
        hints["join_likely"] = True

    return hints