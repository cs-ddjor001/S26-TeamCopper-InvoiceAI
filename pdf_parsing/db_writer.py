from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.invoice import Invoice
from .validator import InvoiceValidator

def normalize_raw_invoice(data:dict) -> dict:
    """Normalizes the LiquidAI output for InvoiceValidator."""
    date_val = data.get("date")
    if isinstance(date_val, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                dt = datetime.strptime(date_val.strip(), fmt)
                data["date"] = dt.strftime("%Y-%m-%d")
                break
            except ValueError:
                continue

    for item in data.get("line_items", []):
        for key in ("unit_price", "total"):
            if key in item and isinstance(item[key], (int, float)):
                item[key] = str(item[key])

    return data


def save_parsed_invoice(parsed):
    parsed = normalize_raw_invoice(parsed)
    parsed = InvoiceValidator.model_validate(parsed)

    if parsed.supplier:
        vendor = Vendors.query.filter_by(name=parsed.supplier).first()
        if not vendor:
            vendor = Vendors(name=parsed.supplier)
            db.session.add(vendor)
            db.session.flush()

    invoice = Invoice(
        po_number=parsed.po_number,
        matched_po_id=None,
        vendor_name=parsed.supplier,
        amount=parsed.amount,
        status=parsed.status or "pending",
        date_issued=datetime.strptime(parsed.date, "%Y-%m-%d") if isinstance(parsed.date, str) else parsed.date,
        confidence_score=None,
    )

    db.session.add(invoice)
    db.session.commit()

    return invoice