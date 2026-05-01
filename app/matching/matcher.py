from app.matching.exact_matcher import match_invoice as match_invoice_exact
from app.matching.fuzzy_matcher import match_by_fields_fuzzy


def match_invoice(invoice):
    """Run the deterministic matching pipeline for an invoice.

    Strategy:
        1. Try exact matching first (PO number or field match)
        2. Fall back to fuzzy weighted matching
        3. Return (None, 0) if no match found

    Returns:
        Tuple of (Purchase_Order, confidence_score) where score is 0-100.
    """
    # 1. Try exact matching first
    po, score = match_invoice_exact(invoice)
    if po:
        return po, score

    # 2. Try fuzzy matching
    po, score = match_by_fields_fuzzy(invoice)
    if po:
        # fuzzy_matcher returns 0-1, scale to 0-100 for consistency
        return po, round(score * 100)

    # 3. No match
    return None, 0