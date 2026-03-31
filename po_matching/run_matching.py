from extensions import db
from models.invoice import Invoice
from po_matching.matcher import match_invoice


def run_matching():
    unmatched = Invoice.query.filter_by(matched_po_id=None).all()
    print(f"Found {len(unmatched)} unmatched invoice(s).")

    matched = 0
    for invoice in unmatched:
        po, score = match_invoice(invoice)
        if po:
            invoice.matched_po_id = po.id
            invoice.confidence_score = score
            matched += 1

    db.session.commit()
    print(f"Matched: {matched}, still unmatched: {len(unmatched) - matched}")
    return len(unmatched), matched
