import re
import pdfplumber
from models.parsed_invoice import ParsedInvoice


def parse_invoice_pdf(filepath):
    with pdfplumber.open(filepath) as pdf:
        text = pdf.pages[0].extract_text()

    po_number = None
    supplier = None
    amount = None
    status = None

    for line in text.split("\n"):
        line = line.strip()

        if line.startswith("PO Number:"):
            raw = line.split(":", 1)[1].strip()
            match = re.search(r"\d+", raw)
            if match:
                po_number = int(match.group())

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

    return ParsedInvoice(
        po_number=po_number,
        supplier=supplier,
        amount=amount,
        status=status,
    )
