import pdfplumber
from datetime import datetime
from pathlib import Path
from models.parsed_invoice import ParsedInvoice


def _resolve_pdf_path(filepath):
    path = Path(filepath)
    if path.is_file():
        return path

    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "data" / "uploads" / path.name,
        project_root / "data" / path.name,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"PDF not found: {filepath}")


def parse_invoice_pdf(filepath):
    resolved_path = _resolve_pdf_path(filepath)

    with pdfplumber.open(str(resolved_path)) as pdf:
        text = pdf.pages[0].extract_text()

    return text