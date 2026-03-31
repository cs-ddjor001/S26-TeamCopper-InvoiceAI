from datetime import datetime
from extensions import db
from models.vendors import Vendors
from models.invoice import Invoice
from models.invoice_line_item import Invoice_Line_Item
from .validator import InvoiceValidator
from decimal import Decimal

def normalize_raw_invoice(data:dict) -> dict:
    """Normalizes the LiquidAI output for InvoiceValidator."""

    if not data.get("date"):
        if isinstance(data.get("invoice_date"), str):
            data["date"] = data["invoice_date"]

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
            if key in item:
                item[key] = str(item[key])
        if "quantity" in item:
            if isinstance(item["quantity"], (int, float)):
                item["quantity"] = float(item["quantity"])

    if not data.get("po_number"):
        customer_po = (
            data.get("purchase_customer", {}).get("customer_po")
            or data.get("purchase_customer", {}).get("customer_number")
            or data.get("customer_purchase_order_number")
        )
        if customer_po:
            data["po_number"] = str(customer_po)

    if not data.get("vendor_name"):
        data["vendor_name"] = "UNKNOWN"
    
    for key in ("subtotal", "tax", "total"):
        if key in data and isinstance(data[key], (int, float)):
            data[key] = float(data[key])

    return data


def save_parsed_invoice(parsed):
    parsed = normalize_raw_invoice(parsed)
    parsed = InvoiceValidator.model_validate(parsed)

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

    for item in parsed.line_items:
        li = Invoice_Line_Item(invoice_id=invoice.id,
                               line_num=None,
                               part_number=None,
                               part_description=item.description,
                               unit_of_measure=None,
                               quantity=item.quantity,
                               unit_price=float(item.unit_price),
                               amt_invoiced=float(item.total),
                               clin=None)
        db.session.add(li)
    db.session.commit()
    return invoice