from extensions import db
from models.invoice import Invoice
from models.matches import Match
from po_matching.ai_matcher import match_invoice_ai


def run_ai_matching():
    """Run AI-based matching on all unmatched invoices using the Qwen model.

    This is a separate pipeline from the deterministic (exact + fuzzy) pipeline
    in run_matching.py. Running both allows direct comparison of approaches.

    For each unmatched invoice:
        1. Send invoice + all POs to Qwen for semantic matching
        2. If a confident match is returned, create a Match record
        3. Update the invoice with the matched PO and confidence score

    Raises:
        ConnectionError: If llama-server is not reachable.
    """
    unmatched = Invoice.query.filter_by(matched_po_id=None).all()
    print(f"Found {len(unmatched)} unmatched invoice(s).")

    matched_count = 0

    for invoice in unmatched:
        po, score = match_invoice_ai(invoice)

        if po and score > 25:
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

            invoice.matched_po_id = po.id
            invoice.confidence_score = score
            invoice.status = "matched"
            matched_count += 1

    db.session.commit()
    print(f"Matched: {matched_count}, still unmatched: {len(unmatched) - matched_count}")
    return len(unmatched), matched_count
