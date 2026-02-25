from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.invoice import Invoice
from po_matching.matcher import match_invoice


def save_parsed_invoice(parsed_invoice):

    vendor = Vendors.query.filter_by(name=parsed_invoice.supplier).first()
    if not vendor:
        vendor = Vendors(name=parsed_invoice.supplier)
        db.session.add(vendor)
        db.session.flush()

    po = match_invoice(parsed_invoice)

    invoice = Invoice(
        po_number=po.id if po else None,
        vendor=vendor.id,
        amount=parsed_invoice.amount,
        status=parsed_invoice.status or "pending",
        date_issued=parsed_invoice.date or datetime.utcnow(),
    )

    db.session.add(invoice)
    db.session.commit()

    return invoice