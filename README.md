# InvoiceAI — Team Copper, Spring 2026

## Members

| GitHub | Name | Email |
|---|---|---|
| cs-ddjor001 | Dusan Djordjevic | ddjor001@odu.edu |
| cmjgrubb | Craig Grubb | cgrub002@odu.edu |
| juuliannd41 | Julian Diaz | jdiaz037@odu.edu |
| MichaelNimitz1995 | Michael Nimitz | mnimi001@odu.edu |
| MinMin5843 | Lynda Salinas Ascanova | lsali002@odu.edu |
| qelson | Quin Elson | qelso001@odu.edu |
| stodd009 | Savannah Todd | stodd009@odu.edu |
| tfull013 | Tommy Fuller | tfull013@odu.edu |

---

## Project Structure

```
S26-TeamCopper-InvoiceAI/
├── app/                        # Flask application package
│   ├── __init__.py             # App factory: create_app()
│   ├── config.py               # Configuration (DB URI, secret key)
│   ├── extensions.py           # Flask-SQLAlchemy db instance
│   ├── models/                 # SQLAlchemy ORM models
│   ├── routes/                 # Flask blueprints (one per page/feature)
│   │   ├── auth.py             # / and /login
│   │   ├── ap.py               # /ap/<username>
│   │   ├── dashboard.py        # /dashboard
│   │   ├── model_trainer.py    # /model-trainer
│   │   └── invoice.py          # /upload-invoice, /run-matching, etc.
│   ├── extraction/             # PDF → structured JSON pipeline
│   ├── parsing/                # Text parsing, validation, DB write
│   ├── matching/               # Invoice-to-PO matching (exact, fuzzy, AI)
│   ├── data_loaders/           # Database seeding utilities
│   └── utils/                  # Shared utilities (quality scoring)
├── templates/                  # Jinja2 HTML templates
├── static/                     # CSS, images, fonts
├── scripts/                    # CLI scripts
│   ├── parse_pdf.py            # Parse and save a single invoice PDF
│   ├── run_matching.py         # Run deterministic matching
│   ├── run_ai_matching.py      # Run AI-based matching
│   └── test_extraction.py      # Test vision extraction on a PDF
├── data/                       # Invoice PDFs, PO CSVs (gitignored)
├── ai_models/                  # Qwen GGUF model files (gitignored)
├── run.py                      # Application entry point
└── requirements.txt
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Delete your old database (if you have one)

Delete `app.db` from the project root if it exists from a previous session.

### 4. Load PO data — this creates the database

```bash
python app/data_loaders/load_po_csv.py
```

This creates all database tables and loads the real ADS purchase order data from `data/ADS_POs_csvs/`.

### 5. Load AP team members and vendors

```bash
python app/data_loaders/user_writer.py
python app/data_loaders/vendor_writer.py
```

`vendor_writer.py` also automatically assigns vendors evenly across AP team members.

### 6. Start the AI model server

```bash
llama-server --model ai_models/Qwen3.5-4B.Q4_K_S.gguf --mmproj ai_models/mmproj-BF16.gguf --port 8080
```

### 7. Run the app

```bash
python run.py
# or
flask --app run run
```

### 8. Login usernames

| Role | Username |
|------|---------|
| Admin dashboard | `sally.admin` |
| AP team demo | `tom.ap` |
| Model trainer | `jim.model` |
| AP team members | username from database (e.g. `anitaknapp`) |

---

## CLI Scripts

All scripts are run from the project root:

```bash
# Parse a single invoice PDF and save to database
python scripts/parse_pdf.py data/ADS_Invoice_PDFs/some_invoice.pdf

# Run deterministic (exact + fuzzy) matching on all unmatched invoices
python scripts/run_matching.py

# Run AI-based matching using the Qwen model
python scripts/run_ai_matching.py

# Test vision extraction on a PDF (requires llama-server running)
python scripts/test_extraction.py data/ADS_Invoice_PDFs/some_invoice.pdf
```

---

## Prerequisites

### Install llama.cpp

```bash
winget install llama.cpp
```

### Download model files

Download from HuggingFace and place both files in `ai_models/`:
- `Qwen3.5-4B.Q4_K_S.gguf`
- `mmproj-BF16.gguf`

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLAMA_SERVER_URL` | `http://localhost:8080/v1` | URL of the llama-server |
| `LLAMA_MODEL` | auto-detected | Override the model name sent to the server |

```bash
# Example: use a different port
set LLAMA_SERVER_URL=http://localhost:9090/v1
```
