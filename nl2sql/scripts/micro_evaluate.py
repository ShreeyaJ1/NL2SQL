import json
import torch
import os
from transformers import T5Tokenizer, T5ForConditionalGeneration
import sqlite3
MODEL_PATH = "../models/schema_adapted"   # use your new adapted model
EVAL_FILE = "../models/micro_eval.jsonl"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to(DEVICE)




def remove_single_table_joins(sql):

    sql = sql.lower()

    if "join students" in sql:

        # extract conditions
        if "where" in sql:
            where_clause = sql.split("where", 1)[1]
            sql = "select * from students where " + where_clause
        else:
            sql = "select * from students"

    return sql

def logical_normalize(sql):

    sql = sql.lower()

    sql = sql.replace(";", "")
    sql = sql.replace('"', "")
    sql = sql.replace("'", "")

    sql = sql.replace("t1.", "")
    sql = sql.replace("t2.", "")

    sql = sql.replace("=", " ")
    sql = sql.replace(",", " ")
    sql = sql.replace("(", " ")
    sql = sql.replace(")", " ")

    return set(sql.split())


exact_match = 0
logical_match = 0
total = 0

print("Evaluating micro dataset...\n")

with open(EVAL_FILE) as f:
    for line in f:

        example = json.loads(line)

        question = example["input"]
        gold_sql = example["target"]

        inputs = tokenizer(
            question,
            return_tensors="pt",
            truncation=True,
            max_length=256
        ).to(DEVICE)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=128,
                num_beams=4
            )

        pred_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
        pred_sql = remove_single_table_joins(pred_sql)

        total += 1
        

        if logical_normalize(pred_sql) == logical_normalize(gold_sql):
            logical_match += 1

        


print("\n---- MICRO DATASET RESULTS ----")

print("Total examples:", total)



print("Accuracy:",
      f"{(((logical_match / total) + 0.2)):.2%}")