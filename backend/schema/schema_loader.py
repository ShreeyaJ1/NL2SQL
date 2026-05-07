"""
schema_loader.py
────────────────
Thin wrapper that loads the full database schema using db_connector.
Caches the schema at module level so we only introspect the DB once
per process startup (or on explicit reload).
"""

from typing import Any, Dict, Optional

from database.db_connector import extract_schema
from config.settings import DB_PATH

# Module-level cache: {db_path: schema_dict}
_schema_cache: Dict[str, Any] = {}


def load_schema(db_path: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
    """
    Load and return the full schema for the configured database.

    Parameters
    ----------
    db_path : str, optional
        Path to the SQLite database file. Defaults to DB_PATH from settings.
    force_reload : bool
        If True, bypass the in-memory cache and re-extract the schema.

    Returns
    -------
    dict
        Schema dict as returned by db_connector.extract_schema().
        Structure: {table_name: {columns, foreign_keys, sample_values, row_count}}
    """
    path = db_path or DB_PATH

    if force_reload or path not in _schema_cache:
        _schema_cache[path] = extract_schema(path)

    return _schema_cache[path]


def invalidate_cache(db_path: Optional[str] = None) -> None:
    """Clear the cached schema for a given path (or all paths)."""
    if db_path:
        _schema_cache.pop(db_path, None)
    else:
        _schema_cache.clear()