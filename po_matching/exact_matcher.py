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

    # 2. Match by vendor + amount as fallback
    po = match_by_fields(invoice)
    if po:
        return po, 85  # High but not 100 — no PO number confirmation

    return None, 0


def match_to_po_directly(po_number):
    """Find a PO by exact PO number match."""
    return Purchase_Order.query.filter_by(po_number=po_number).first()


def match_by_fields(invoice):
    """Find a PO by matching vendor and amount.

    Note: Uses vendor (FK ID) and amount since these are the fields
    that exist on the current models. If vendor_name and po_date are
    added to the models later, update this query accordingly.
    """
    return Purchase_Order.query.filter_by(
        vendor=invoice.vendor,
        amount=invoice.amount,
    ).first()