from flask import Flask, request, jsonify

from schema.schema_loader import load_schema
from schema.prompt_builder import build_prompt
from schema.schema_linker import link_schema

from model.inference import generate_sql

from sql.sql_postprocess import clean_sql
from sql.sql_validator import is_safe_sql
from sql.sql_executor import execute_sql
from sql.sql_repair import repair_sql
from sql.query_analyser import analyze_query
from sql.rule_engine import generate_sql_rule_based

from sql.sql_verifier import verify_sql

from config.settings import DEFAULT_COMPLEX_MESSAGE

DB_PATH = "database/sample.db"

app = Flask(__name__)


@app.route("/query", methods=["POST"])
def query():

    # -----------------------------
    # 1 GET QUESTION
    # -----------------------------

    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400


    # -----------------------------
    # 2 RULE-BASED SQL
    # -----------------------------

    sql = generate_sql_rule_based(question)
    if sql is not None:
        try:
            
            if not verify_sql(DB_PATH, sql):
                raise Exception("Unsafe SQL from rule engine")
            

            results = execute_sql(DB_PATH, sql)

            if results is not None:

                return jsonify({
                "question": question,
                "generated_sql": sql,
                "results": results
            })

        except Exception:
            pass
    
    print("model")


    # -----------------------------
    # 3 MODEL FALLBACK
    # -----------------------------

    schema = load_schema(DB_PATH)

    schema = link_schema(question, schema)

    hints = analyze_query(question)

    prompt = build_prompt(question, schema, hints)

    raw_sql = generate_sql(prompt)

    sql = clean_sql(raw_sql)


    # -----------------------------
    # 4 VALIDATE SQL
    # -----------------------------

    if not is_safe_sql(sql):
        return jsonify({"message": DEFAULT_COMPLEX_MESSAGE})
    
    # if not verify_sql(DB_PATH, sql):
    #     return jsonify({"message": DEFAULT_COMPLEX_MESSAGE})


    # -----------------------------
    # 5 EXECUTE MODEL SQL
    # -----------------------------

    try:

        results = execute_sql(DB_PATH, sql)

    except Exception:

        repaired_sql = repair_sql(sql)

        try:

            results = execute_sql(DB_PATH, repaired_sql)

            sql = repaired_sql

        except Exception:

            return jsonify({"message": DEFAULT_COMPLEX_MESSAGE})


    return jsonify({
        "question": question,
        "generated_sql": sql,
        "results": results
    })


if __name__ == "__main__":
    app.run(debug=True)