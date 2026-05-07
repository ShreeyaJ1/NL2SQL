"""
app.py
──────
NL2SQL Flask API Server

Endpoints
─────────
  POST /api/query     — Translate NL question → SQL → execute → return results
  GET  /api/schema    — Return the schema of the configured database
  GET  /api/health    — Model + database health check

Configuration
─────────────
  Edit backend/config/settings.py to change DB_PATH (the SQLite database to query).
  Users interact with the system only through natural language questions.

Pipeline (per /api/query request)
──────────────────────────────────
  1. Rule engine  — handles trivially simple "show all X" queries instantly
  2. Schema load  — extract full schema from the configured SQLite DB
  3. Schema link  — prune schema to only the tables/cols relevant to the question
  4. Query hints  — NLP-based intent extraction (aggregation, sort, limit...)
  5. Prompt build — Spider-style serialisation for the T5 model
  6. Inference    — T5-Large beam search → raw SQL
  7. Post-process — Extract + normalise SQL from model output
  8. Safety check — Reject any non-SELECT or mutation-containing SQL
  9. Verify       — Check table names exist in schema
 10. Execute      — Run on SQLite, return (columns, rows)
 11. Repair       — If execution fails, fuzzy-fix identifiers and retry
"""

import os
import sys
import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Pipeline imports ──────────────────────────────────────────────────────────
from schema.schema_loader   import load_schema
from schema.schema_linker   import link_schema
from schema.prompt_builder  import build_prompt, build_debug_prompt

from model.inference        import generate_sql, model_is_available, get_active_model_name

from sql.rule_engine        import generate_sql_rule_based
from sql.query_analyser     import analyze_query
from sql.sql_postprocess    import clean_sql
from sql.sql_validator      import is_safe_sql
from sql.sql_verifier       import verify_sql
from sql.sql_repair         import repair_sql
from sql.sql_executor       import run_sql

from utils.response_formatter import format_success, format_error

from config.settings import DB_PATH, DEFAULT_ERROR_MESSAGE

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nl2sql")

app = Flask(__name__)
CORS(app)   # Allow cross-origin requests (useful when connecting a frontend later)


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Return the status of the model and database connection."""
    db_ok = False
    db_tables = 0
    try:
        schema = load_schema(DB_PATH)
        db_ok = True
        db_tables = len(schema)
    except Exception as e:
        log.warning("DB health check failed: %s", e)

    return jsonify({
        "status":       "ok" if db_ok else "degraded",
        "model_loaded": model_is_available(),
        "model_name":   get_active_model_name(),
        "db_path":      DB_PATH,
        "db_reachable": db_ok,
        "db_tables":    db_tables,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Schema inspection
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/schema", methods=["GET"])
def schema_view():
    """
    Return the full schema of the configured database.

    Response
    --------
    {
      "db_path": "...",
      "tables": {
        "table_name": {
          "columns": [{"name", "type", "pk", "notnull"}, ...],
          "foreign_keys": [...],
          "sample_values": {"col": ["v1", "v2", ...]},
          "row_count": 123
        }
      }
    }
    """
    try:
        schema = load_schema(DB_PATH)
        return jsonify({"db_path": DB_PATH, "tables": schema})
    except Exception as e:
        log.error("Schema load failed: %s", e)
        return jsonify({"error": f"Could not load schema: {e}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Main query endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/query", methods=["POST"])
def query():
    """
    Translate a natural language question into SQL and execute it.

    Request body (JSON)
    -------------------
    {
      "question": "How many students are enrolled in each major?"
    }

    Response (success)
    ------------------
    {
      "success":   true,
      "question":  "...",
      "sql":       "SELECT major, COUNT(*) FROM students GROUP BY major",
      "source":    "model",
      "columns":   ["major", "COUNT(*)"],
      "rows":      [["Computer Science", 42], ["Physics", 17]],
      "row_count": 2
    }

    Response (failure)
    ------------------
    {
      "success":  false,
      "question": "...",
      "message":  "Could not generate a valid SQL query...",
      "stage":    "validation"
    }
    """
    # ── Parse request ─────────────────────────────────────────────────────
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "No question provided. Send JSON: {\"question\": \"...\"}"}), 400

    log.info("Question: %s", question)

    # ── Load schema ───────────────────────────────────────────────────────
    try:
        full_schema = load_schema(DB_PATH)
    except Exception as e:
        log.error("Could not load schema: %s", e)
        return jsonify(format_error(question, f"Database error: {e}", stage="schema_load")), 500

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 1: Rule engine (instant, zero-cost for simple queries)
    # ─────────────────────────────────────────────────────────────────────
    sql = generate_sql_rule_based(question, schema=full_schema)

    if sql is not None:
        log.info("[Rule engine] Generated: %s", sql)

        if verify_sql(sql, full_schema):
            try:
                columns, rows = run_sql(sql, DB_PATH)
                log.info("[Rule engine] Success — %d rows", len(rows))
                return jsonify(format_success(
                    question, sql, columns, rows, source="rule_engine"
                ))
            except Exception as e:
                log.warning("[Rule engine] Execution failed: %s — falling through to model", e)

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 2: Model-based generation
    # ─────────────────────────────────────────────────────────────────────
    if not model_is_available():
        return jsonify(format_error(
            question,
            "Model is not loaded. Check server logs for download/load errors.",
            stage="model_unavailable",
        )), 503

    # 2a. Schema linking — prune to relevant tables
    linked_schema = link_schema(question, full_schema)
    log.info(
        "[Schema linker] Tables selected: %s",
        list(linked_schema.keys()),
    )

    # 2b. Query intent hints
    hints = analyze_query(question)
    if hints:
        log.info("[Query analyser] Hints: %s", hints)

    # 2c. Build model prompt
    prompt = build_prompt(question, linked_schema, hints=hints)
    log.debug("[Prompt]\n%s", build_debug_prompt(question, linked_schema, hints=hints))

    # 2d. Model inference
    raw_output = generate_sql(prompt)
    log.info("[Model] Raw output: %s", raw_output)

    if not raw_output:
        return jsonify(format_error(question, DEFAULT_ERROR_MESSAGE, stage="inference")), 422

    # 2e. Post-process
    sql = clean_sql(raw_output)
    log.info("[Post-process] Clean SQL: %s", sql)

    if not sql:
        return jsonify(format_error(
            question, DEFAULT_ERROR_MESSAGE, stage="postprocess"
        )), 422

    # 2f. Safety validation
    if not is_safe_sql(sql):
        log.warning("[Validator] Rejected unsafe SQL: %s", sql)
        return jsonify(format_error(
            question,
            "Generated SQL contains unsafe operations and was rejected.",
            sql=sql,
            stage="validation",
        )), 422

    # 2g. Schema verification (table names)
    if not verify_sql(sql, full_schema):
        log.warning("[Verifier] SQL references unknown tables — attempting repair")
        sql = repair_sql(sql, full_schema)
        log.info("[Repair] Repaired SQL: %s", sql)

        if not verify_sql(sql, full_schema):
            return jsonify(format_error(
                question, DEFAULT_ERROR_MESSAGE, sql=sql, stage="verification"
            )), 422

    # 2h. Execute
    try:
        columns, rows = run_sql(sql, DB_PATH)
        log.info("[Executor] Success — %d rows", len(rows))
        return jsonify(format_success(question, sql, columns, rows, source="model"))

    except Exception as exec_error:
        log.warning("[Executor] Failed: %s — attempting SQL repair", exec_error)

        # 2i. Repair and retry
        repaired_sql = repair_sql(sql, full_schema)
        log.info("[Repair] Repaired SQL: %s", repaired_sql)

        if repaired_sql != sql:
            try:
                columns, rows = run_sql(repaired_sql, DB_PATH)
                log.info("[Repair+Executor] Success — %d rows", len(rows))
                return jsonify(format_success(
                    question, repaired_sql, columns, rows, source="model+repair"
                ))
            except Exception as repair_error:
                log.error("[Repair+Executor] Also failed: %s", repair_error)

        return jsonify(format_error(
            question, DEFAULT_ERROR_MESSAGE, sql=sql, stage="execution"
        )), 422


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run with debug=False in production
    app.run(host="0.0.0.0", port=5000, debug=True)