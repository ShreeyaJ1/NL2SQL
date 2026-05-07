# NL2SQL — Transformer-Based Natural Language to SQL Engine

A sophisticated **Natural Language to SQL (NL2SQL)** system built as a B.Tech CSE (AI/ML) final semester project.

Converts natural language questions into SQL queries, executes them on a configured SQLite database, and returns structured results — with **no LLM API key required**. Everything runs locally.

---

## Architecture

```
User NL Question
       │
       ▼
┌──────────────────────────┐
│ 1. Rule Engine (fast)    │  → handles trivial "show all X" queries instantly
└──────────┬───────────────┘
           │ (if no match)
           ▼
┌──────────────────────────┐
│ 2. Schema Loader         │  → extracts tables/columns/FKs/samples from SQLite
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 3. Schema Linker (NLP)   │  → prunes to relevant tables (token overlap + fuzzy)
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 4. Query Analyser        │  → detects aggregation, sort, limit, negation, etc.
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 5. Prompt Builder        │  → Spider-style serialization for the T5 model
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 6. T5-Large NL2SQL Model │  → tscholak/3vnuv1vf (Spider fine-tuned, local)
│    Beam Search (k=4)     │     ~79% exact match on Spider dev set
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 7. SQL Post-Processor    │  → extract + normalise SQL from raw model output
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 8. Safety Validator      │  → reject any non-SELECT or mutation SQL
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│ 9. Schema Verifier       │  → verify table names exist in actual schema
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│10. SQL Repair            │  → fuzzy-match wrong identifiers → auto-correct
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│11. SQL Executor          │  → run on SQLite, return (columns, rows)
└──────────────────────────┘
```

---

## Repository Structure

```
NL2SQL/
├── backend/
│   ├── app.py                    # Flask API (3 endpoints)
│   ├── config/
│   │   └── settings.py           # ← SET DB_PATH HERE
│   ├── database/
│   │   ├── db_connector.py       # Unified SQLite layer (schema + execution)
│   │   ├── create_database.py    # Sample DB creation script
│   │   └── sample.db             # Sample students database
│   ├── schema/
│   │   ├── schema_loader.py      # Cached schema extraction
│   │   ├── schema_linker.py      # NLP-based schema pruning (rapidfuzz)
│   │   └── prompt_builder.py     # Spider-style prompt serializer
│   ├── model/
│   │   ├── load_model.py         # T5-Large Spider model loader
│   │   └── inference.py          # Beam search SQL generation
│   ├── sql/
│   │   ├── rule_engine.py        # Generic fast-path rule engine
│   │   ├── query_analyser.py     # NLP intent extraction
│   │   ├── sql_postprocess.py    # SQL extraction + normalization
│   │   ├── sql_repair.py         # Fuzzy schema-aware SQL repair
│   │   ├── sql_validator.py      # Safety validation (SELECT-only)
│   │   ├── sql_verifier.py       # Schema-level table verification
│   │   └── sql_executor.py       # SQLite query executor
│   └── utils/
│       └── response_formatter.py # Structured JSON response builder
│
├── nl2sql/
│   ├── models/                   # Downloaded/trained models stored here
│   └── scripts/                  # Training and evaluation scripts
│
├── test_pipeline.py              # End-to-end pipeline smoke test
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sarthakj0304/NL2SQL.git
cd NL2SQL
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:
- `flask`, `flask-cors` — API server
- `torch`, `transformers`, `sentencepiece` — T5 model
- `accelerate` — efficient model loading
- `rapidfuzz` — fuzzy schema linking
- `sentence-transformers` — semantic similarity (optional enhancement)
- `sqlparse` — SQL parsing and validation
- `datasets` — for training scripts

---

## Configure Your Database

Edit `backend/config/settings.py` and set `DB_PATH` to your SQLite database:

```python
# backend/config/settings.py
DB_PATH = "database/sample.db"   # ← change this to your .db file path
```

That's it — the system will **automatically**:
- Extract all tables, columns, types, and foreign keys
- Sample values for schema enrichment
- Work with any schema, any number of tables

---

## Download the Spider Dataset (for Fine-Tuning Only)

> **Not required for inference.** The pre-trained model runs without Spider.
> Only needed if you want to fine-tune the model from scratch.

**Option A — HuggingFace (easiest):**
```bash
pip install huggingface_hub
python -c "from datasets import load_dataset; ds = load_dataset('yale-nlp/spider'); print('Downloaded!')"
```

**Option B — Official website:**
1. Visit: https://yale-lily.github.io/spider
2. Fill the form → download `spider.zip`
3. Extract to `data/spider/`

Structure after extraction:
```
data/spider/
├── train_spider.json
├── dev.json
├── tables.json
└── database/
```

---

## Run the Server

```bash
cd backend
python app.py
```

On **first run**, the T5-Large Spider model (~3 GB) will download automatically from HuggingFace and be cached locally. Subsequent runs load from cache instantly.

Server starts at: `http://127.0.0.1:5000`

---

## API Endpoints

### `POST /api/query` — Main NL2SQL endpoint

```json
// Request
{ "question": "How many students study each major?" }

// Response (success)
{
  "success": true,
  "question": "How many students study each major?",
  "sql": "SELECT major, COUNT(*) FROM students GROUP BY major",
  "source": "model",
  "columns": ["major", "COUNT(*)"],
  "rows": [["Computer Science", 5], ["Physics", 3]],
  "row_count": 2
}

// Response (failure)
{
  "success": false,
  "question": "...",
  "message": "Could not generate a valid SQL query...",
  "stage": "validation"
}
```

### `GET /api/schema` — Inspect the connected database

```json
{
  "db_path": "database/sample.db",
  "tables": {
    "students": {
      "columns": [{"name": "id", "type": "INTEGER", "pk": true}, ...],
      "foreign_keys": [],
      "sample_values": {"name": ["Alice", "Bob"], "grade": ["A", "B"]},
      "row_count": 15
    }
  }
}
```

### `GET /api/health` — Server + model status

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "tscholak/3vnuv1vf",
  "db_path": "database/sample.db",
  "db_reachable": true,
  "db_tables": 1
}
```

---

## Run Pipeline Tests

Test all stages without starting the server:

```bash
python test_pipeline.py
```

---

## Example Queries

```
List all students
Show all students
How many students study each major?
What is the average age of students in Computer Science?
Show students older than 21 with grade A
Who are the top 5 youngest students?
Count students with grade B
```

---

## Model Details

| Property | Value |
|---|---|
| **Model** | `tscholak/3vnuv1vf` (PICARD T5-Large) |
| **Parameters** | 770M |
| **Training data** | Spider NL2SQL benchmark |
| **Spider accuracy** | ~79% exact match |
| **Inference** | Beam search, k=4 |
| **Hardware needed** | CPU + 8 GB RAM (16 GB recommended) |
| **GPU** | Optional (CUDA auto-detected) |
| **API key** | None — fully local |

---

## Technologies Used

| Component | Technology |
|---|---|
| Web framework | Flask + Flask-CORS |
| NL2SQL model | HuggingFace Transformers (T5-Large) |
| Schema linking | rapidfuzz, token overlap |
| SQL parsing | sqlparse |
| Database | SQLite (via Python stdlib) |
| Inference | PyTorch (beam search) |

---

## Limitations

- Optimised for **SQLite** databases
- Very complex multi-table JOINs with deep nesting may have lower accuracy
- Model accuracy depends on how closely the question phrasing matches Spider training data
- First run requires ~3 GB download for the model weights
