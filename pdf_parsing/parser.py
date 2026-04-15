import re
import pdfplumber
from pathlib import Path
from po_matching.ai_matcher import AIMatcher
from datetime import datetime
from models.parsed_invoice import ParsedInvoice


def parse_invoice_pdf(filepath):
    """Extract text from a PDF with pdfplumber, then use Qwen to structure it.

    Returns:
        Dict with structured invoice fields (invoice_number, vendor_name, date,
        po_number, subtotal, tax, total, line_items) ready for InvoiceValidator.

    Raises:
        FileNotFoundError: If the PDF cannot be found.
        ConnectionError: If llama-server is not reachable.
    """
    resolved_path = _resolve_pdf_path(filepath)

    with pdfplumber.open(str(resolved_path)) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    raw_text = "\n\n".join(pages_text).strip()

    if not raw_text:
        raise ValueError(
            f"No text could be extracted from {resolved_path.name}. "
            "The PDF may be image-based (scanned). Only text-based PDFs are supported."
        )

    ai = AIMatcher()
    return ai.extract_invoice_from_text(raw_text)
    with pdfplumber.open(filepath) as pdf:
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
