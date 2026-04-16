from extensions import db
from models.invoice import Invoice
from models.matches import Match
from po_matching.matcher import match_invoice
from utils.invoice_quality_score import compute_invoice_quality

def run_matching():
    """Run deterministic matching on all unmatched invoices.

    For each unmatched invoice:
        1. Run the matching pipeline (exact → fuzzy)
        2. If a match is found above threshold, create a Match record
        3. Update the invoice with the matched PO and confidence score
    """
    unmatched = Invoice.query.filter_by(matched_po_id=None).all()
    print(f"Found {len(unmatched)} unmatched invoice(s).")

    matched_count = 0

    for invoice in unmatched:
        po, score = match_invoice(invoice)

        if po and score > 25:
            # Check for existing match to prevent duplicates
            existing = Match.query.filter_by(
                invoice_id=invoice.id,
                po_id=po.id,
            ).first()

            if existing is None:
                match = Match(
                    invoice_id=invoice.id,
                    po_id=po.id,
                    confidence_score=score,
                )
                db.session.add(match)

            # Update the invoice with the best match
            invoice.matched_po_id = po.id
            invoice.confidence_score = score
            invoice.status = "matched"
            matched_count += 1

    db.session.commit()
    print(f"Matched: {matched_count}, still unmatched: {len(unmatched) - matched_count}")
    return len(unmatched), matched_count