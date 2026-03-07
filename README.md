
# Transformer-Based NL2SQL System

This project implements a **Transformer-based Natural Language to SQL (NL2SQL) system** capable of converting natural language questions into SQL queries, executing them on a database, and returning results.

The system uses a **fine-tuned T5 model** trained on the **Spider dataset**, followed by **schema adaptation fine-tuning** for the target database.

The project also includes a **Flask backend** that allows users to query the system through an API.

---

# Project Architecture

The system pipeline works as follows:

```
Natural Language Question
        ↓
Schema Injection
        ↓
Fine-tuned Transformer (T5)
        ↓
SQL Post-processing
        ↓
SQL Safety Validation
        ↓
SQLite Query Execution
        ↓
Results Returned
```

---

# Repository Structure

```
.
├── backend/
│   ├── app.py
│   ├── database/
│   │   └── sample.db
│   ├── model/
│   ├── schema/
│   ├── sql/
│   └── utils/
│
├── nl2sql/
│   ├── scripts/
│   │   ├── train_model.py
│   │   ├── micro_finetune.py
│   │   ├── evaluate_micro.py
│   │   └── generate_micro_dataset.py
│   └── models/
│
├── data/
│   └── spider/
│
├── requirements.txt
├── README.md
└── .gitignore
```

Important notes:

* The **Spider dataset is not included** in this repository due to size.
* **Trained models are not included**.
* All datasets and models can be **generated locally using the provided scripts**.

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/sarthakj0304/NL2SQL.git
cd NL2SQL
```

---

## 2. Create Conda Environment

```bash
conda create -n major-project python=3.10
conda activate major-project
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Download Spider Dataset

The Spider dataset must be downloaded manually.

Download it from the official website:

[https://yale-lily.github.io/spider](https://yale-lily.github.io/spider)

After downloading, place the files inside:

```
data/spider/
```

Your folder structure should look like:

```
data/
 └── spider/
      ├── database/
      ├── tables.json
      ├── train_spider.json
      └── dev.json
```

---

# Train the Base NL2SQL Model

The base model is trained using the Spider dataset.

Run:

```bash
python nl2sql/scripts/train_model.py
```

This will:

* Load the Spider dataset
* Train a T5 model
* Save the trained model to:

```
nl2sql/models/advanced_final/
```

Training time depends on hardware.

---

# Generate Schema Adaptation Dataset

The project includes a **micro dataset generator** that creates synthetic NL-SQL pairs for the target schema.

Run:

```bash
python nl2sql/scripts/generate_micro_dataset.py
```

This will generate:

```
nl2sql/models/micro_train.jsonl
nl2sql/models/micro_eval.jsonl
```

These datasets are used for **schema-specific fine-tuning**.

---

# Run Micro Fine-Tuning

Micro fine-tuning adapts the model to the **students database schema** used in the backend.

Run:

```bash
python nl2sql/scripts/micro_finetune.py
```

This will:

* load the base trained model
* fine-tune on the generated dataset
* save the adapted model to:

```
nl2sql/models/schema_adapted/
```

Training typically takes **2–3 minutes on an M1/M2 Mac**.

---

# Evaluate the Adapted Model

Run:

```bash
python nl2sql/scripts/evaluate_micro.py
```

This evaluates the model using logical SQL comparison on the micro evaluation dataset.

Example output:

```
---- MICRO DATASET RESULTS ----

Total examples: 60
Accuracy: 52.33%
```

---

# Run the Backend API

The backend allows users to query the NL2SQL system through a REST API.

Start the Flask server:

```bash
python backend/app.py
```

The server will start at:

```
http://127.0.0.1:5000
```

---

# Query the System

Send a POST request to:

```
/query
```

Example request:

```json
{
  "question": "Show students with grade A"
}
```

Example response:

```json
{
  "question": "Show students with grade A",
  "generated_sql": "SELECT * FROM students WHERE grade='A'",
  "results": [...]
}
```

---

# Example Queries

```
List all students
Show student names
Show students with grade A
Show students studying Physics
Show students older than 21
```

---



# Technologies Used

* Python
* PyTorch
* HuggingFace Transformers
* T5 (Text-to-Text Transformer)
* SQLite
* Flask

---

# Limitations

* The model may hallucinate joins due to training on multi-table Spider schemas.
* Accuracy depends on schema similarity with the training dataset.
* The current system supports **single-table schemas best**.

---

