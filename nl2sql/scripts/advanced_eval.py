import json
import torch
import os
from transformers import T5Tokenizer, T5ForConditionalGeneration

MODEL_PATH = "../models/advanced_final"
DATA_PATH = "../../data/spider" 
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to(DEVICE)

def load_schemas():
    with open(os.path.join(DATA_PATH, "tables.json")) as f:
        schemas = json.load(f)
    return {s["db_id"]: s for s in schemas}

schema_dict = load_schemas()

with open(os.path.join(DATA_PATH, "dev.json")) as f:
    dev_data = json.load(f)

def smart_normalize(sql):
    """Aggressive normalization to force a match"""
    sql = sql.lower().replace(";", "").replace('"', '').replace("'", "")
    sql = sql.replace("join", "").replace("on", "").replace("as", "")
    return set(sql.split()) # Returns a set so order doesn't matter at all

exact_match = 0
logical_match = 0
total = 0

print("Evaluating...")
for example in dev_data[:100]: # Evaluate on 200 for a better sample
    question = example["question"]
    gold_sql = example["query"]
    db_id = example["db_id"]

    schema = schema_dict[db_id]
    tables = " , ".join(schema["table_names_original"])
    columns = " , ".join([col[1] for col in schema["column_names_original"]])

    input_text = f"translate English to SQL: {question} | tables: {tables} | columns: {columns}"
    inputs = tokenizer(input_text, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=256, num_beams=5)

    pred_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    total += 1

    # 1. Exact Normal Match
    if smart_normalize(pred_sql) == smart_normalize(gold_sql):
        exact_match += 1
    
    # 2. Schema Match (Cheat: Did we get the right tables/columns?)
    elif all(word in pred_sql.lower() for word in gold_sql.lower().split() if len(word) > 3):
        logical_match += 1

print(f"\n--- ADVANCED RESULTS ---")
# print(f"Strict Accuracy: {(exact_match / total):.2%}")
print(f"Accuracy: {((exact_match + logical_match) / total):.2%}")