import sys
from app import app
from pdf_parsing.parser import parse_invoice_pdf
from pdf_parsing.db_writer import save_parsed_invoice

# Default to sample.pdf if no path given
pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"

with app.app_context():
    print(f"Parsing: {pdf_path}")
    parsed = parse_invoice_pdf(pdf_path)

    print(f"  PO Number (extracted): {parsed.po_number}")
    print(f"  Supplier:              {parsed.supplier}")
    print(f"  Amount:                {parsed.amount}")
    print(f"  Status:                {parsed.status}")
    print(f"  Date Issued:           {parsed.date}")

    invoice = save_parsed_invoice(parsed)
    print(
        f"\nSaved to DB — Invoice id: {invoice.id}, "
        f"PO number (doc): {invoice.po_number}, "
        f"Matched PO id: {invoice.matched_po_id}, "
        f"Confidence: {invoice.confidence_score}, "
        f"Vendor id: {invoice.vendor}, "
        f"Invoice Date: {invoice.date_issued}"
    )