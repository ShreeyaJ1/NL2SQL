import torch
from model.load_model import model, tokenizer
from config.settings import DEVICE, MAX_INPUT_LENGTH, MAX_OUTPUT_LENGTH, BEAM_SIZE

def generate_sql(prompt):

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_LENGTH
    ).to(DEVICE)

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_length=MAX_OUTPUT_LENGTH,
            num_beams=BEAM_SIZE,
            early_stopping=True
        )

    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return sql