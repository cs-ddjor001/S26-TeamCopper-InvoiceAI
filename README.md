# InvoiceAI — Team Copper, Spring 2026

## Members

| GitHub | Name | Email |
|---|---|---|
| cs-ddjor001 | Dusan Djordjevic | ddjor001@odu.edu |
| cmjgrubb | Craig Grubb | cgrub002@odu.edu |
| juuliannd41 | Julian Diaz | jdiaz037@odu.edu |
| MichaelNimitz1995 | Michael Nimitza | mnimi001@odu.edu |
| MinMin5843 | Lynda Salinas Ascanova | lsali002@odu.edu |
| qelson | Quin Elson | qelso001@odu.edu |
| stodd009 | Savannah Todd | stodd009@odu.edu |
| tfull013 | Tommy Fuller | tfull013@odu.edu |

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

```bash
# Just delete app.db from the project root
```

The database is not committed to the repo. If you have a stale `app.db` from a previous session, delete it before continuing.

### 4. Load PO data — this creates the database

```bash
python Purchase_order_writer/load_po_csv.py
```

This is the required first step. It creates all database tables and loads the real ADS purchase order data from `data/ADS POs csvs/`. The app cannot run meaningfully without POs in the database.

### 5. Run the app

```bash
python app.py
# or
flask run
```

### 6. Usernames
tom.ap
sally.admin
jim.model
---

### 7. Upload Invoices
After ensuring the liquid AI model is running (instructions below), use the Upload Invoice button to upload invoices,
then run matching. 

## Liquid AI Invoice Extraction (Vision Model)

Uses the Liquid AI LFM2.5-VL-1.6B vision model to extract structured data from invoice PDFs via a locally-running llama-server.

### Prerequisites

1. Install llama.cpp:
   ```bash
   winget install llama.cpp
   ```

2. Download the models from HuggingFace (LiquidAI/LFM2.5-VL-1.6B-GGUF):
   - `LFM2.5-VL-1.6B-Q8_0.gguf` — main vision model
   - `mmproj-LFM2.5-VL-1.6b-Q8_0.gguf` — multimodal projector ("eyes" that read images)

   Place both in the `ai_models/` directory.

3. Start the llama server:
   ```bash
   llama-server --model ai_models/LFM2.5-VL-1.6B-Q8_0.gguf --mmproj ai_models/mmproj-LFM2.5-VL-1.6b-Q8_0.gguf --port 8080
   ```

### Usage

```bash
python test_extraction.py data/ADSdata/some_invoice.pdf
```

To use a different server address:
```bash
set LLAMA_SERVER_URL=http://localhost:9090/v1
```
