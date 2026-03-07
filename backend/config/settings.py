import torch



MODEL_PATH = "../nl2sql/models/schema_adapted"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

MAX_INPUT_LENGTH = 256
MAX_OUTPUT_LENGTH = 128

BEAM_SIZE = 4

ALLOWED_SQL = ["select"]

DEFAULT_COMPLEX_MESSAGE = "Sorry, this question is too complex for the demo system."