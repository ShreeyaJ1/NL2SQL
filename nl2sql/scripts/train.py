import os
import torch
from transformers import (
    T5Tokenizer, 
    T5ForConditionalGeneration, 
    Seq2SeqTrainer, 
    Seq2SeqTrainingArguments, 
    DataCollatorForSeq2Seq
)
from datasets import load_dataset

# 1. CRITICAL M1 ENV VARS
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

MODEL_NAME = "t5-small"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"Using device: {DEVICE}")

# 2. Load Dataset
dataset = load_dataset("json", data_files={
    "train": "../models/train.jsonl",
    "validation": "../models/dev.jsonl"
})

tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)

# 3. Optimized Preprocessing
def preprocess(examples):
    model_inputs = tokenizer(
        examples["input"],
        max_length=256, # Enough for Spider schema
        truncation=True,
        padding="max_length"
    )

    labels = tokenizer(
        text_target=examples["target"],
        max_length=128,
        truncation=True,
        padding="max_length"
    )

    # Use -100 to ignore padding in loss calculation
    label_ids = [
        [(l if l != tokenizer.pad_token_id else -100) for l in label]
        for label in labels["input_ids"]
    ]
    
    model_inputs["labels"] = label_ids
    return model_inputs

# 1. Shuffle the data so you get a mix of all databases
# 2. Select only 1500 examples (Enough for 20-30% accuracy on T5-small)
tokenized_dataset = dataset.map(preprocess, batched=True, remove_columns=dataset["train"].column_names)

train_subset = tokenized_dataset["train"].shuffle(seed=42).select(range(1500))
eval_subset = tokenized_dataset["validation"].select(range(200))

# 4. Load Model and Move to MPS
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEVICE)

training_args = Seq2SeqTrainingArguments(
    output_dir="../models/checkpoints",
    learning_rate=3e-4,             # Higher LR since we are training on less data
    per_device_train_batch_size=8,  # Increased because max_length is now 256
    gradient_accumulation_steps=2,  # Effective batch size of 16
    num_train_epochs=7,             # Only 2 passes over the subset
    gradient_checkpointing=True,
    optim="adamw_torch",
    eval_strategy="no",
    save_strategy="no",
    dataloader_num_workers=0,
    dataloader_pin_memory=False,
    predict_with_generate=True,
    report_to="none"
)

# 6. Use a Data Collator
# This handles padding dynamically, which is more efficient than manual padding
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
model.to("mps")
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_subset,     # Use the subset here!
    eval_dataset=eval_subset,       # Use the subset here!
    data_collator=data_collator,
    processing_class=tokenizer
)

# 7. Train and Save
trainer.train()
trainer.save_model("../models/final_model")
tokenizer.save_pretrained("../models/final_model")