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
        for currentMatch in po_and_score:
            if currentMatch.score > 25:
                match = Match(
                    invoice_id = invoice.id,
                    po_id = currentMatch.row.id,
                    confidence_score = currentMatch.score,
                    matchFound = True
                )
                db.session.add(match)

        if matchFound:
            matched +=1

    db.session.commit()
    print(f"Matched: {matched}, still unmatched: {len(unmatched) - matched}")
    return len(unmatched), matched
