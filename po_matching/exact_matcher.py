from models.purchase_orders import Purchase_Order


def match_invoice(invoice):
    """Attempt an exact match for an invoice against POs in the database.

    Returns:
        Tuple of (Purchase_Order, score) or (None, 0) if no match found.
    """
    # 1. Direct PO number match — strongest signal
    if invoice.po_number:
        po = match_to_po_directly(invoice.po_number)
        if po:
            return po, 100

    # 2. Match by vendor/date signals as fallback
    po = match_by_fields(invoice)
    if po:
        return po, 85  # High but not 100 — no PO number confirmation

    return None, 0


def match_to_po_directly(po_number):
    """Find a PO by exact PO number match."""
    return Purchase_Order.query.filter_by(po_number=po_number).first()


def match_by_fields(invoice):
    """Find a PO by matching fields that exist on Purchase_Order.

    Current schema has vendor_name and po_date (but no amount column).
    Strategy:
    1) vendor_name + exact date when invoice date exists
    2) vendor_name only, newest PO first
    """
    vendor_name = getattr(invoice, "vendor_name", None)
    if not vendor_name:
        return None

    query = Purchase_Order.query.filter_by(vendor_name=vendor_name)

    invoice_date = getattr(invoice, "date_issued", None)
    if invoice_date is not None:
        po = query.filter(Purchase_Order.po_date == invoice_date).first()
        if po:
            return po

    return query.order_by(Purchase_Order.po_date.desc()).first()