from app.models import Purchase_Order
from app.matching.fuzzy_matcher import price_within_tolerance, match_by_fields_fuzzy


def match_invoice(invoice):
    """Attempt an exact match for an invoice against POs in the database.

    Returns:
        Tuple of (Purchase_Order, score) or (None, 0) if no match found.
    """
    if not invoice.po_number:
        # No PO number at all → go straight to fuzzy
        po, fuzzy_score = match_by_fields_fuzzy(invoice)
        if po:
            return po, fuzzy_score
        return None, 0

    # 1. Strong exact (PO + ADS line items) 
    po = Purchase_Order.query.filter_by(po_number=invoice.po_number).first()
    if po and invoice_has_matching_line_item(invoice, po):
        return po, 100
    
    # 2. Fuzzy match
    po, fuzzy_score = match_by_fields_fuzzy(invoice)
    if po:
        return po, fuzzy_score

    return None, 0


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