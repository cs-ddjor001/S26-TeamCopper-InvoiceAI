from po_matching.exact_matcher import match_invoice as match_invoice_exact
from po_matching.fuzzy_matcher import match_by_fields_fuzzy
from models.invoice import Invoice
from models.purchase_orders import Purchase_Order

def match_invoice(invoice):
    # For each invoice, calculate a confidence score and pair it with the compared PO
    po_and_score = {}

    results = Purchase_Order.query.all()
    for po in results:
        score = 0
        if invoice.po_number == po.po_number:
            # print("PO number match")
            score = score+50
        if invoice.vendor == po.vendor:
            # print("Vendor match")
            score = score+20
        if invoice.amount == po.amount:
            # print("AMount match")
            score = score+15
        if invoice.date_issued == po.date_issued:
            # print("Date match")
            score = score+15
        po_and_score.update({po:score})
    
    return po_and_score
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

