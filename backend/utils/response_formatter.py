def format_success(question, sql, results):

    return {
        "status": "success",
        "question": question,
        "generated_sql": sql,
        "row_count": len(results),
        "results": results
    }


def format_error(message):

    return {
        "status": "error",
        "message": message
    }