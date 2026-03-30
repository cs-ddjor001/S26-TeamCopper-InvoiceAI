from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.invoice import Invoice
from .validator import InvoiceValidator


def save_parsed_invoice(parsed):

    parsed = InvoiceValidator.model_validate(parsed)

    vendor = Vendors.query.filter_by(name=parsed.supplier).first()
    if not vendor:
        vendor = Vendors(name=parsed.supplier)
        db.session.add(vendor)
        db.session.flush()

    invoice = Invoice(
        po_number=parsed.po_number,
        matched_po_id=None,
        vendor=vendor.id,
        amount=parsed.amount,
        status=parsed.status or "pending",
        date_issued=datetime.strptime(parsed.date, "%Y-%m-%d") if isinstance(parsed.date, str) else parsed.date,
        confidence_score=None,
    )

    db.session.add(invoice)
    db.session.commit()

    return invoice