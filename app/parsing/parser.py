import re
import pdfplumber
from datetime import datetime
from app.models.parsed_invoice import ParsedInvoice


def parse_invoice_pdf(filepath):
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