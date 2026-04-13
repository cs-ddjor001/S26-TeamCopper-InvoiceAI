import pdfplumber
from datetime import datetime
from pathlib import Path
from models.parsed_invoice import ParsedInvoice


def _resolve_pdf_path(filepath):
    """Resolve a PDF path, supporting both absolute paths and bare filenames."""
    path = Path(filepath)
    if path.is_file():
        return path

    # If only a filename is provided, search known project PDF folders.
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

    po_number = None
    supplier = None
    amount = None
    status = None
    date = None

    for line in text.split("\n"):
        line = line.strip()

        if line.startswith("PO Number:"):
            raw = line.split(":", 1)[1].strip()
            try:
                po_number = int(raw)
            except ValueError:
                pass

        elif line.startswith("Supplier:"):
            supplier = line.split(":", 1)[1].strip()

        elif line.startswith("Amount:"):
            raw = line.split(":", 1)[1].strip().replace("$", "").replace(",", "")
            try:
                amount = float(raw)
            except ValueError:
                pass

        elif line.startswith("Status:"):
            status = line.split(":", 1)[1].strip()

        elif line.startswith("Date Issued:"):
            raw = line.split(":", 1)[1].strip()
            try:
                date = datetime.strptime(raw, "%Y-%m-%d")
            except ValueError:
                date = None

    return ParsedInvoice(
        po_number=po_number,
        supplier=supplier,
        amount=amount,
        status=status,
        date=date,
    )