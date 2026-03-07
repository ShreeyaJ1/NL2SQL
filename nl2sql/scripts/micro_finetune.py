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

MODEL_PATH = "../models/advanced_final"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

dataset = load_dataset(
    "json",
    data_files={
        "train": "../models/micro_train.jsonl",
        "eval": "../models/micro_eval.jsonl"
    }
)

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to(DEVICE)


def preprocess(ex):

    model_inputs = tokenizer(
        ex["input"],
        max_length=256,
        truncation=True,
        padding="max_length"
    )

    labels = tokenizer(
        text_target=ex["target"],
        max_length=128,
        truncation=True,
        padding="max_length"
    )

    model_inputs["labels"] = [
        (l if l != tokenizer.pad_token_id else -100)
        for l in labels["input_ids"]
    ]

    return model_inputs


train_data = dataset["train"].map(preprocess)
eval_data = dataset["eval"].map(preprocess)


training_args = Seq2SeqTrainingArguments(

    output_dir="../models/schema_adapted",

    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,

    num_train_epochs=2,

    learning_rate=2e-5,

   
    eval_strategy="epoch",
    save_strategy="no",

    report_to="none"
)


trainer = Seq2SeqTrainer(

    model=model,
    args=training_args,

    train_dataset=train_data,
    eval_dataset=eval_data,

    data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),

    processing_class=tokenizer
)


print("Starting micro fine-tuning...")

trainer.train()




model.save_pretrained("../models/schema_adapted")
tokenizer.save_pretrained("../models/schema_adapted")

print("Schema-adapted model saved.")