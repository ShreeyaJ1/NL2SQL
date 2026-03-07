import json
import os

DATA_PATH = "../../data/spider"

def load_spider(file):
    with open(os.path.join(DATA_PATH, file)) as f:
        return json.load(f)

def load_schemas():
    with open(os.path.join(DATA_PATH, "tables.json")) as f:
        schemas = json.load(f)
    return {s["db_id"]: s for s in schemas}

def convert_to_t5_format(data, schema_dict, output_file):
    with open(output_file, "w") as f:
        for example in data:
            question = example["question"]
            sql = example["query"].lower().replace(";", "")
            db_id = example["db_id"]

            schema = schema_dict[db_id]

            tables = " , ".join(schema["table_names_original"])
            columns = " , ".join([col[1] for col in schema["column_names_original"]])

            input_text = (
                f"translate English to SQL: {question} "
                f"| tables: {tables} "
                f"| columns: {columns}"
            )

            f.write(json.dumps({
                "input": input_text,
                "target": sql
            }) + "\n")

if __name__ == "__main__":
    schema_dict = load_schemas()

    train_data = load_spider("train_spider.json")
    dev_data = load_spider("dev.json")

    convert_to_t5_format(train_data, schema_dict, "../models/train.jsonl")
    convert_to_t5_format(dev_data[:500], schema_dict, "../models/dev.jsonl")

    print("Data prepared.")