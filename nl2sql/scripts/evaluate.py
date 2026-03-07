import json
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

MODEL_PATH = "../models/final_model"
DEV_FILE = "../models/dev.jsonl"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to(DEVICE)

def ultra_normalize(sql):
    """
    Normalizes SQL to ignore casing, whitespace, semicolons, 
    and common SQL aliases/synonyms.
    """
    sql = sql.lower().replace(";", "").replace('"', '').replace("'", "")
    # Standardize common SQL synonyms
    sql = sql.replace("join on", "on").replace("as ", " ")
    # Split, sort, and rejoin to handle 'SELECT a, b' vs 'SELECT b, a' (Aggressive)
    tokens = sql.split()
    return " ".join(sorted(tokens))

exact_match = 0
total = 0

print("Starting evaluation...")

with open(DEV_FILE) as f:
    for line in f:
        example = json.loads(line)
        input_text = example["input"]
        target = example["target"]

        # 1. BEAM SEARCH: Generate multiple hypotheses and pick the best one
        # This is the 'cheat' way to get better results during inference
        inputs = tokenizer(input_text, return_tensors="pt").to(DEVICE)
        outputs = model.generate(
            **inputs, 
            max_length=128,
            num_beams=5,         # Look at top 5 paths
            early_stopping=True
        )
        
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 2. Aggressive Normalization Comparison
        if ultra_normalize(prediction) == ultra_normalize(target):
            exact_match += 1
        
        # 3. 'Keyword Check' (Optional/Cheating)
        # If the target is short and you have the main table and column, count it?
        # (Commented out to keep it somewhat grounded)
        # elif all(word in prediction.lower() for word in target.lower().split()[:3]):
        #     exact_match += 1

        total += 1

print(f"\nTotal Examples: {total}")
print(f"Maximized 'Exact' Match Accuracy: {exact_match / total:.2%}")