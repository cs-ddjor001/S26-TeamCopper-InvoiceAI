from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.purchase_orders import Purchase_Order
from models.invoice import Invoice


def save_parsed_invoice(parsed_invoice):
    # Get or create vendor by name
    vendor = Vendors.query.filter_by(name=parsed_invoice.supplier).first()
    if not vendor:
        vendor = Vendors(name=parsed_invoice.supplier)
        db.session.add(vendor)
        db.session.flush()  # assigns vendor.id before we reference it below

    # Create a purchase order for this invoice
    po = Purchase_Order(
        vendor=vendor.id,
        amount=parsed_invoice.amount,
        date_issued=datetime.utcnow(),
    )
    db.session.add(po)
    db.session.flush()  # assigns po.id

    # Create the invoice
    invoice = Invoice(
        po_number=po.id,
        vendor=vendor.id,
        amount=parsed_invoice.amount,
        status=parsed_invoice.status or "pending",
    )
    db.session.add(invoice)
    db.session.commit()

    return invoice
