from models.purchase_orders import Purchase_Order
from po_matching.fuzzy_matcher import price_within_tolerance


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
    po = Purchase_Order.query.filter_by(po_number=po_number).first()
    if not po:
        return None
    
    if not invoice_has_matching_line_item(invoice, po):
        return None
    
    return po



def match_by_fields(invoice):
    """Find a PO by matching fields that exist on Purchase_Order.

    Current schema has vendor_name and po_date (but no amount column).
    Strategy:
    1) vendor_name + exact date when invoice date exists
    2) vendor_name only, newest PO first
    """
    if not invoice.po_number:
        return None
    
    po = Purchase_Order.query.filter_by(po_number = invoice.po_number).first()
    if not po:
        return None
    if not invoice_has_matching_line_item(invoice, po):
        return None
    
    return po


def invoice_has_matching_line_item(invoice, po):
    """Check for line item matching.
    1) Part number must match
    2) The unit price must be within tolerance
    """
    invoice_items = invoice.line_items or []
    po_items = po.line_items or []

    for inv in invoice_items:
        for po_item in po_items:

            # Part number required
            if not inv.part_number or not po_item.part_number:
                continue
            if inv.part_number.strip() != po_item.part_number.strip():
                continue

            # Unit price tolerance required
            if not price_within_tolerance(inv.unit_price, po_item.unit_price):
                continue
            # If we reach here → ADS rules satisfied
            return True

    return False