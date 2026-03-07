import os
import torch
from datasets import load_dataset
from transformers import (
    T5Tokenizer, 
    T5ForConditionalGeneration, 
    Seq2SeqTrainer, 
    Seq2SeqTrainingArguments, 
    DataCollatorForSeq2Seq
)

# 1. Setup
MODEL_NAME = "cssupport/t5-small-awesome-text-to-sql"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

dataset = load_dataset("json", data_files={"train": "../models/train.jsonl"})
tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEVICE)

def preprocess(ex):
    model_inputs = tokenizer(ex["input"], max_length=256, truncation=True, padding="max_length")
    labels = tokenizer(text_target=ex["target"], max_length=128, truncation=True, padding="max_length")
    model_inputs["labels"] = [[(l if l != tokenizer.pad_token_id else -100) for l in label] for label in labels["input_ids"]]
    return model_inputs

# INCREASED DATA: 4000 examples is the "sweet spot" for Spider fine-tuning
train_data = dataset["train"].shuffle(seed=42).select(range(4000)).map(preprocess, batched=True)

# 2. POWER TRAINING ARGS
training_args = Seq2SeqTrainingArguments(
    output_dir="../models/advanced_checkpoints",
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,  # Effective batch size of 16
    num_train_epochs=5,             # INCREASED: Need at least 5 epochs
    learning_rate=5e-4,             # Higher learning rate for T5
    lr_scheduler_type="cosine",     # Smoothly lower LR for better accuracy
    weight_decay=0.01,
    optim="adamw_torch",            # Stable for MPS
    
    # Speed & Memory
    gradient_checkpointing=True,    # Saves VRAM
    save_strategy="no",
    report_to="none",
    dataloader_num_workers=0,
    predict_with_generate=True
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    processing_class=tokenizer
)

print("Starting the Power-Tune (Estimated 15-20 mins)...")
trainer.train()

# 3. SAVE THE FINAL MODEL
model.save_pretrained("../models/advanced_final")
tokenizer.save_pretrained("../models/advanced_final")
print("Done! Now run the evaluation script.")