from po_matching.exact_matcher import match_invoice_exact
from po_matching.fuzzy_matcher import (
    match_to_po_fuzzy,
    match_by_fields_fuzzy
)

def match_invoice(invoice):
    # 1. Try exact matching first
    po, score = match_invoice_exact(invoice)
    if po:
        return po, score

    # 2. Try fuzzy PO matching
    if invoice.po_number:
        po, score = match_to_po_fuzzy(invoice.po_number)
        if po:
            return po, int(score * 100)

    # 3. Try fuzzy field matching
    po, score = match_by_fields_fuzzy(invoice)
    if po:
        return po, int(score * 100)

    return None, None

