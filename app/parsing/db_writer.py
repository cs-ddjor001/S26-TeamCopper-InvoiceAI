from datetime import datetime
from app.extensions import db
from app.models.vendors import Vendors
from app.models.invoice import Invoice
from app.models.invoice_line_item import Invoice_Line_Item
from .validator import InvoiceValidator


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

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
        # Check flat keys the model commonly uses
        customer_po = (
            data.get("purchase_customer", {}).get("customer_po")
            or data.get("purchase_customer", {}).get("customer_number")
            or data.get("customer_purchase_order_number")
            or data.get("customer_po_number")
            or data.get("customer_po_nbr")
            or data.get("customer_po_no")
            or data.get("cust_po")
            or data.get("purchase_order_number")
            or data.get("purchase_order_no")
            or data.get("order_number")
            or data.get("order_no")
            or data.get("customer_reference")
            or data.get("your_reference")
            or data.get("reference_number")
        )
        # Check nested paths the model sometimes uses
        if not customer_po:
            for nested_key in ("payment_instructions", "payment_info", "billing_info", "order_info"):
                nested = data.get(nested_key)
                if isinstance(nested, dict):
                    customer_po = (
                        nested.get("purchase_order_number")
                        or nested.get("po_number")
                        or nested.get("customer_po")
                        or nested.get("order_number")
                        or nested.get("reference_number")
                    )
                    if not customer_po and isinstance(nested.get("bank_information"), dict):
                        customer_po = (
                            nested["bank_information"].get("purchase_order_number")
                            or nested["bank_information"].get("po_number")
                            or nested["bank_information"].get("customer_po")
                        )
                    if customer_po:
                        break
        if customer_po:
            data["po_number"] = str(customer_po)

    for key in ("subtotal", "tax", "total"):
        if key in data and isinstance(data[key], (int, float)):
            data[key] = float(data[key])

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
        po_number=parsed.po_number_int,
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
        quantity = _safe_float(item.quantity)
        unit_price = _safe_float(item.unit_price)
        amt_invoiced = _safe_float(item.total)

        # Ignore rows with no usable values to avoid storing model noise.
        if not item.description and quantity is None and unit_price is None and amt_invoiced is None:
            continue

        li = Invoice_Line_Item(invoice_id=invoice.id,
                               line_num=None,
                               part_number=None,
                               part_description=item.description,
                               unit_of_measure=None,
                               quantity=quantity,
                               unit_price=unit_price,
                               amt_invoiced=amt_invoiced,
                               clin=None)
        db.session.add(li)
    db.session.commit()
    return invoice