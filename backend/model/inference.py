"""
inference.py
────────────
SQL generation from a prompt using the loaded NL2SQL model.

Uses beam search for better SQL quality:
  - num_beams=4: explore 4 candidate sequences simultaneously
  - early_stopping=True: stop when all beams hit EOS
  - no_repeat_ngram_size=3: prevents repetitive output
"""

import torch
from typing import Optional

from model.load_model import model, tokenizer, active_model_name
from config.settings import DEVICE, MAX_INPUT_LENGTH, MAX_OUTPUT_LENGTH, BEAM_SIZE


def generate_sql(prompt: str) -> Optional[str]:
    """
    Generate SQL from a structured prompt using beam search.

    Parameters
    ----------
    prompt : str
        The model input string (Spider format from prompt_builder).

    Returns
    -------
    str or None
        The raw generated SQL string, or None if the model is unavailable.
    """
    if model is None or tokenizer is None:
        return None

    # Tokenise input
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_LENGTH,
        padding=False,
    ).to(DEVICE)

    # Generate with beam search
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_OUTPUT_LENGTH,
            num_beams=BEAM_SIZE,
            early_stopping=True,
            no_repeat_ngram_size=3,
            length_penalty=1.0,   # Neutral: don't bias toward short or long
        )

    # Decode — skip special tokens like <pad>, </s>
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql.strip()


def model_is_available() -> bool:
    """Return True if the model loaded successfully."""
    return model is not None and tokenizer is not None


def get_active_model_name() -> str:
    """Return the name of the currently loaded model."""
    return active_model_name or "none"