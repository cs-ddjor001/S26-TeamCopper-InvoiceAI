from rapidfuzz import fuzz
from models import Purchase_Order
import re


def normalize(text):
    """Normalize text for fuzzy comparison — uppercase, strip punctuation/whitespace."""
    if not text:
        return ""
    text = str(text).upper().strip()
    text = re.sub(r"[\s\-_:;,.]", "", text)
    return text


def fuzzy_score(a, b):
    """Return a similarity score between 0 and 1 for two strings."""
    if not a or not b:
        return 0
    return fuzz.ratio(normalize(a), normalize(b)) / 100.0


def price_within_tolerance(invoice_price, po_price):
    """Check if the invoice price is within acceptable tolerance of the PO price.

    Tolerance tiers (based on ADS guidance):
        - PO price > $5,000: 1% tolerance
        - PO price < $100:   5% tolerance
        - Otherwise:         2% tolerance (standard)
    """
    if invoice_price is None or po_price is None:
        return False
    if po_price == 0:
        return invoice_price == 0

    tolerance = 0.02
    if po_price > 5000:
        tolerance = 0.01
    elif po_price < 100:
        tolerance = 0.05

    diff = abs(invoice_price - po_price) / po_price
    return diff <= tolerance


def get_top_candidates(invoice, n=10):
    """Return the top N POs by fuzzy score, regardless of threshold.

    Used to pre-filter candidates before sending to the AI matcher, keeping
    the prompt within the model's context window.

    Returns:
        List of Purchase_Order objects sorted by descending score (up to n).
    """
    candidates = Purchase_Order.query.all()
    scored = []

    for po in candidates:
        invoice_items = getattr(invoice, "line_items", [])
        po_items = getattr(po, "line_items", [])

        total_score = 0

        score_po = fuzzy_score(str(invoice.po_number or ""), str(po.po_number))
        total_score += 0.50 * score_po

        score_line = compute_line_item_score(invoice_items, po_items)
        total_score += 0.45 * score_line

        score_date = 1 if invoice.date_issued == getattr(po, "date_issued", None) else 0
        total_score += 0.05 * score_date

        scored.append((po, total_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [po for po, _ in scored[:n]]


def match_by_fields_fuzzy(invoice, threshold=0.55):
    """Score all POs against the invoice using weighted fuzzy matching.

    Weights:
        PO number:              50%
        Part number/description: 45%
        Date:                    5%

    Returns:
        Tuple of (best_po, best_score) or (None, 0) if no match above threshold.
    """
    candidates = Purchase_Order.query.all()

    best_po = None
    best_score = 0

    for po in candidates:
        if normalize(invoice.po_number or "") != normalize(po.po_number):
            continue

        invoice_items = getattr(invoice, "line_items", [])
        po_items = getattr(po, "line_items", [])

        if not has_valid_line_item_match(invoice_items, po_items):
            continue

        total_score = 0

        # PO number (50% weight)
        score_po = fuzzy_score(str(invoice.po_number or ""), str(po.po_number))
        total_score += 0.50 * score_po

        # Part number and unit price matching (45% weight)
        score_line = compute_line_item_score(invoice_items, po_items)
        total_score += 0.45 * score_line

        # Date (5% weight)
        score_date = 1 if invoice.date_issued == getattr(po, "date_issued", None) else 0
        total_score += 0.05 * score_date

        if total_score > best_score:
            best_score = total_score
            best_po = po

    if best_score >= threshold:
        return best_po, best_score

    return None, 0

def has_valid_line_item_match(invoice_items, po_items):
    """ADS rules:
       1) Part number must match
       2) Unit price must be within tolerance
    """
    for inv in invoice_items:
        for po in po_items:
            if inv.part_number and po.part_number:
                if normalize(inv.part_number) == normalize(po.part_number):
                    if price_within_tolerance(inv.unit_price, po.unit_price):
                        return True
    return False


def compute_line_item_score(invoice_items, po_items):
    """Fuzzy part description scoring."""
    best = 0
    for inv in invoice_items:
        for po in po_items:
            score = max(
                fuzzy_score(inv.part_description, po.part_description),
                fuzzy_score(inv.part_number, po.part_number),
            )
            best = max(best, score)
    return best