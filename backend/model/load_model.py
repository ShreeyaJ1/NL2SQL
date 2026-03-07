import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from config.settings import MODEL_PATH, DEVICE

print("Loading NL2SQL model...")

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)

model = model.to(DEVICE)
model.eval()

print("Model loaded successfully.")