from extensions import db
from app import app
from models import Invoice, Match
from po_matching.ai_matcher import match_invoice_ai
from utils.invoice_quality_score import compute_invoice_quality

def run_ai_matching():
    """Run AI-based matching on all unmatched invoices using the Qwen model.

    This is a separate pipeline from the deterministic (exact + fuzzy) pipeline
    in run_matching.py. Running both allows direct comparison of approaches.

    For each unmatched invoice:
        1. Send invoice + candidate POs to Qwen for semantic matching
        2. Apply invoice quality score to the AI confidence
        3. If a confident match is returned, create a Match record
        4. Update the invoice with the matched PO and confidence score

    Raises:
        ConnectionError: If llama-server is not reachable.
    """
    unmatched = Invoice.query.filter_by(ai_matched_po_id=None).all()
    print(f"Found {len(unmatched)} unmatched invoice(s).")

    matched_count = 0

    for invoice in unmatched:
        po, match_score = match_invoice_ai(invoice)

        if not po:
            continue
    
        invoice_quality_score = invoice.quality_score or 100
        final_score = round(match_score * (invoice_quality_score / 100))

        if final_score > 25:
            existing = Match.query.filter_by(
                invoice_id=invoice.id,
                po_id=po.id,
            ).first()

            if existing is None:
                match = Match(
                    invoice_id = invoice.id,
                    po_id = po.id,
                    confidence_score = final_score,
                )
                db.session.add(match)

            invoice.ai_matched_po_id = po.id
            invoice.ai_confidence_score = final_score
            invoice.status = "matched"
            if po.vendor_name:
                invoice.vendor_name = po.vendor_name
            matched_count += 1

    db.session.commit()
    print(f"Matched: {matched_count}, still unmatched: {len(unmatched) - matched_count}")
    return len(unmatched), matched_count
