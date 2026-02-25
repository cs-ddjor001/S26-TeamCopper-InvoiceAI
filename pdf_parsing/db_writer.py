from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.invoice import Invoice


def save_parsed_invoice(parsed_invoice):

    vendor = Vendors.query.filter_by(name=parsed_invoice.supplier).first()
    if not vendor:
        vendor = Vendors(name=parsed_invoice.supplier)
        db.session.add(vendor)
        db.session.flush()

    invoice = Invoice(
        po_number=parsed_invoice.po_number,
        matched_po_id=None,
        vendor=vendor.id,
        amount=parsed_invoice.amount,
        status=parsed_invoice.status or "pending",
        date_issued=parsed_invoice.date or datetime.utcnow(),
        confidence_score=None,
    )

    db.session.add(invoice)
    db.session.commit()

    return invoice