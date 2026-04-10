from extensions import db
from models.invoice import Invoice
from models.matches import Match
from po_matching.matcher import match_invoice


def run_matching():
    unmatched = Invoice.query.filter_by(matched_po_id=None).all()
    print(f"Found {len(unmatched)} unmatched invoice(s).")
    matched = 0
    for invoice in unmatched:
        matchFound = False
        po_and_score = match_invoice(invoice)
        for po, score in po_and_score.items():
            # prevents duplicate matches if the matcher is run multiple times
            # a shoddy solution really, would prefer not to query each time
            if score > 25 and Match.query.filter_by(invoice_id=invoice.id, po_id=po.id) is None:
                match = Match(
                    invoice_id = invoice.id,
                    po_id = po.id,
                    confidence_score = score,
                )
                matchFound = True
                db.session.add(match)

        if matchFound:
            po, score = match_invoice(invoice)
        if po:
            invoice.matched_po_id = po.id
            invoice.confidence_score = score
            invoice.status = "complete"
            matched += 1

    db.session.commit()
    print(f"Matched: {matched}, still unmatched: {len(unmatched) - matched}")
    return len(unmatched), matched
