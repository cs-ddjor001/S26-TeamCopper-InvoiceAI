from po_matching.exact_matcher import match_invoice as match_invoice_exact
from po_matching.fuzzy_matcher import match_by_fields_fuzzy
from models.invoice import Invoice
from models.purchase_orders import Purchase_Order

def match_invoice(invoice):
    # 1. Try exact matching first
    po, score = match_invoice_exact(invoice)
    if po:
        return po, score

    # 2. Try fuzzy matching
    po, score = match_by_fields_fuzzy(invoice)
    if po:
        return po, score

    # 3. No match
    return None, 0

