"""
sql_executor.py
───────────────
Executes validated SQL against the configured SQLite database.
Wraps db_connector.execute_query() with error handling and logging.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from database.db_connector import execute_query
from config.settings import DB_PATH, MAX_RESULTS


def run_sql(
    sql: str,
    db_path: Optional[str] = None,
    limit: Optional[int] = None,
) -> Tuple[List[str], List[List[Any]]]:
    """
    Execute `sql` against the database at `db_path`.

    Parameters
    ----------
    sql : str
        A valid, safe SQL query (already validated by sql_validator).
    db_path : str, optional
        Path to the SQLite file. Defaults to settings.DB_PATH.
    limit : int, optional
        Max rows to return. Defaults to settings.MAX_RESULTS.

    Returns
    -------
    (column_names, rows) : Tuple[List[str], List[List[Any]]]

    Raises
    ------
    sqlite3.Error
        On database execution failure (caller should handle this).
    """
    path  = db_path  or DB_PATH
    limit = limit    or MAX_RESULTS
    return execute_query(path, sql, limit=limit)