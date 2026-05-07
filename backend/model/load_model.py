"""
load_model.py
─────────────
Loads the NL2SQL model from HuggingFace.

Model: tscholak/3vnuv1vf
  - T5-Large (770M parameters) fine-tuned on Spider NL2SQL benchmark
  - ~79% exact-match accuracy on Spider dev set
  - Spider input format: "<question> | <db_id> | <serialized_schema>"
  - Cached locally after first download (~3 GB)

Requirements: torch >= 2.6 (fixes CVE-2025-32434)
"""

import sys
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    T5Tokenizer,
    T5ForConditionalGeneration,
)

from config.settings import MODEL_NAME, FALLBACK_MODEL_NAME, DEVICE

# ─────────────────────────────────────────────────────────────────────────────
# Model loading
# ─────────────────────────────────────────────────────────────────────────────

def _load(model_name: str):
    """Attempt to load tokenizer + model from HuggingFace hub."""
    print(f"[NL2SQL] Loading model: {model_name}")
    print(f"[NL2SQL] Device: {DEVICE}")

    # ── Tokenizer ─────────────────────────────────────────────────────────
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    except Exception:
        tokenizer = T5Tokenizer.from_pretrained(model_name)

    # ── Model (three-tier loading strategy) ──────────────────────────────
    model = None

    # Tier 1: prefer safetensors (no torch.load, no CVE)
    try:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        print("[NL2SQL] Loaded via safetensors.")
    except Exception:
        pass

    # Tier 2: torch >= 2.6 fixed torch.load — standard load should work now
    if model is None:
        try:
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                low_cpu_mem_usage=True,
            )
            print("[NL2SQL] Loaded via standard from_pretrained.")
        except Exception:
            pass

    # Tier 3: explicit T5 class (skip AutoModel resolver)
    if model is None:
        model = T5ForConditionalGeneration.from_pretrained(
            model_name,
            low_cpu_mem_usage=True,
        )
        print("[NL2SQL] Loaded via T5ForConditionalGeneration.")

    model = model.to(DEVICE)
    model.eval()
    print(f"[NL2SQL] Model ready on {DEVICE}.")
    return tokenizer, model


# ─────────────────────────────────────────────────────────────────────────────
# Load at startup — primary → fallback → None
# ─────────────────────────────────────────────────────────────────────────────

tokenizer = None
model = None
active_model_name = None

try:
    print(f"[NL2SQL] Starting model load: {MODEL_NAME}")
    tokenizer, model = _load(MODEL_NAME)
    active_model_name = MODEL_NAME
    print(f"[NL2SQL] [OK] Primary model loaded: {MODEL_NAME}")

except Exception as primary_error:
    print(f"[NL2SQL] Primary model failed: {primary_error}")
    print(f"[NL2SQL] Trying fallback: {FALLBACK_MODEL_NAME}")

    try:
        tokenizer, model = _load(FALLBACK_MODEL_NAME)
        active_model_name = FALLBACK_MODEL_NAME
        print(f"[NL2SQL] [OK] Fallback model loaded: {FALLBACK_MODEL_NAME}")

    except Exception as fallback_error:
        print(f"[NL2SQL] [FAIL] Fallback also failed: {fallback_error}")
        print("[NL2SQL] Server will run without model. Only rule engine will work.")