"""
schema_linker.py
────────────────
NLP-based schema linking for NL2SQL.

Given a natural language question and a full database schema, this module
identifies the MOST RELEVANT tables and columns to include in the model
prompt — avoiding context bloat that degrades generation accuracy.

Pipeline
────────
1. Tokenise the question (lower-cased word tokens).
2. For each (table, column) pair, compute a relevance score using:
     a. Exact token overlap between question tokens and the name.
     b. Fuzzy partial-ratio match (rapidfuzz) for typos / abbreviations.
     c. Synonym expansion for common NL patterns
        ("how many" → COUNT, "average" → AVG, etc.).
3. Keep the top-K tables (by aggregate column scores).
4. For small schemas (≤ 3 tables, ≤ 20 total columns) return everything —
   there's no point pruning when the schema already fits in the prompt.
"""

import re
from typing import Any, Dict, List, Set, Tuple

from rapidfuzz import fuzz

from config.settings import MAX_RELEVANT_TABLES, SCHEMA_LINK_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# Synonym / alias expansion
# ─────────────────────────────────────────────────────────────────────────────

# Common NL patterns that imply specific SQL constructs or column types.
# These help the linker surface aggregate columns even when not named directly.
_NL_SYNONYMS: Dict[str, List[str]] = {
    "how many":  ["count", "num", "number", "total", "id"],
    "count":     ["count", "num", "number", "total", "id"],
    "total":     ["total", "sum", "amount", "revenue", "price", "cost", "salary"],
    "average":   ["avg", "average", "mean", "salary", "price", "score", "rating"],
    "avg":       ["avg", "average", "mean", "salary", "price", "score", "rating"],
    "maximum":   ["max", "highest", "largest", "top", "salary", "price", "score"],
    "minimum":   ["min", "lowest", "smallest", "salary", "price", "score"],
    "oldest":    ["age", "dob", "birth", "date", "year"],
    "youngest":  ["age", "dob", "birth", "date", "year"],
    "recent":    ["date", "year", "month", "time", "created", "updated"],
    "latest":    ["date", "year", "month", "time", "created", "updated"],
    "name":      ["name", "title", "label", "first", "last", "full"],
    "location":  ["location", "city", "state", "country", "address", "region"],
    "email":     ["email", "mail", "contact"],
    "phone":     ["phone", "mobile", "tel", "contact"],
}


def _expand_tokens(tokens: List[str]) -> Set[str]:
    """Expand question tokens with synonyms to improve recall."""
    expanded = set(tokens)
    q_text = " ".join(tokens)

    for phrase, synonyms in _NL_SYNONYMS.items():
        if phrase in q_text:
            expanded.update(synonyms)

    return expanded


# ─────────────────────────────────────────────────────────────────────────────
# Tokenisation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> List[str]:
    """Lower-case and split text into alphanumeric tokens (min length 2)."""
    return [t for t in re.findall(r"\b[a-z0-9]+\b", text.lower()) if len(t) >= 2]


def _split_identifier(identifier: str) -> List[str]:
    """
    Split a snake_case or camelCase identifier into component words.
    e.g. "customer_id" → ["customer", "id"]
         "firstName"   → ["first", "name"]
    """
    # snake_case
    parts = identifier.replace("-", "_").split("_")
    # camelCase inside each part
    expanded = []
    for part in parts:
        sub = re.sub(r"([a-z])([A-Z])", r"\1 \2", part)
        expanded.extend(sub.lower().split())
    return [p for p in expanded if len(p) >= 2]


# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────

def _score_name(q_tokens: Set[str], identifier: str) -> float:
    """
    Score how relevant an identifier (table or column name) is to the question.

    Returns a float in [0, 1].
    """
    id_tokens = set(_split_identifier(identifier))
    id_lower  = identifier.lower()

    # 1. Exact token overlap (Jaccard-like)
    overlap = len(q_tokens & id_tokens)
    overlap_score = overlap / max(len(id_tokens), 1)

    # 2. Substring containment — "customer" appears literally in the question
    containment_score = 0.0
    for qt in q_tokens:
        if qt in id_lower or id_lower in qt:
            containment_score = max(containment_score, 1.0)

    # 3. Fuzzy partial match across question tokens
    fuzzy_score = 0.0
    for qt in q_tokens:
        if len(qt) < 3:
            continue
        ratio = fuzz.token_set_ratio(qt, id_lower) / 100.0
        fuzzy_score = max(fuzzy_score, ratio)

    # Weighted combination
    score = (overlap_score * 0.50) + (containment_score * 0.30) + (fuzzy_score * 0.20)
    return min(score, 1.0)


def _table_score(q_tokens: Set[str], table_name: str, table_info: Dict[str, Any]) -> float:
    """
    Aggregate score for an entire table.
    The table's own name contributes, plus the best-scoring column.
    """
    table_name_score = _score_name(q_tokens, table_name)

    col_scores = [
        _score_name(q_tokens, col["name"])
        for col in table_info["columns"]
    ]
    best_col_score = max(col_scores) if col_scores else 0.0

    # Table name match is the dominant signal; column match is supporting
    return max(table_name_score, best_col_score * 0.85)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def link_schema(question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a pruned version of `schema` containing only the tables most
    relevant to `question`.

    Parameters
    ----------
    question : str
        The natural language query from the user.
    schema : dict
        Full schema as returned by schema_loader.load_schema().

    Returns
    -------
    dict
        Pruned schema with the same structure as the input — never empty.
        If schema is small or no table clears the threshold, return all tables.
    """
    total_tables = len(schema)
    total_cols   = sum(len(t["columns"]) for t in schema.values())

    # Small schemas: no pruning needed
    if total_tables <= 3 and total_cols <= 20:
        return schema

    # Tokenise + expand
    raw_tokens  = _tokenise(question)
    q_tokens    = _expand_tokens(raw_tokens)

    # Score every table
    scored: List[Tuple[str, float]] = [
        (tname, _table_score(q_tokens, tname, tinfo))
        for tname, tinfo in schema.items()
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Select top-K tables that clear the threshold
    selected = [
        tname for tname, score in scored[:MAX_RELEVANT_TABLES]
        if score >= SCHEMA_LINK_THRESHOLD
    ]

    # Always include at least the single highest-scoring table
    if not selected and scored:
        selected = [scored[0][0]]

    # Preserve FK-linked tables: if table A references table B, include B
    selected_set = set(selected)
    for tname in list(selected_set):
        for fk in schema[tname].get("foreign_keys", []):
            ref_table = fk["to_table"]
            if ref_table in schema:
                selected_set.add(ref_table)

    return {t: schema[t] for t in schema if t in selected_set}