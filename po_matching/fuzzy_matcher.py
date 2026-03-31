from rapidfuzz import fuzz
from models.purchase_orders import Purchase_Order
import re

def normalize(text):
    if not text:
        return ""
    text = text.upper().strip()
    text = re.sub(r"[\s\-_:;,.]", "", text)
    return text
    
def fuzzy_score(a, b):
    if not a or not b:
        return 0
    return fuzz.ratio(normalize(a), normalize(b)) / 100.00

def match_to_po_fuzzy(po_number, threshold=0.85):
    extracted = normalize(po_number)
    candidates = Purchase_Order.query.all()

    best_po = None
    best_score = 0

    for po in candidates:
        score = fuzzy_score(extracted, po.po_number)
        if score > best_score:
            best_score = score
            best_po = po
        
    if best_score >= threshold:
        return best_po, best_score
    
    return None, None

def match_by_fields_fuzzy(invoice, threshold=0.75):
    candidates = Purchase_Order.query.all()

    best_po = None
    best_score = 0

    for po in candidates:
        score_vendor = fuzzy_score(invoice.vendor, po.vendor)
        score_amount = 1.0 if invoice.amount == po.amount else 0.0
        score_date = 1.0 if invoice.date_issued == po.date_issued else 0.0

        total_score = (0.6 * score_vendor) + (0.2 * score_amount) + (0.2 * score_date)

        if total_score > best_score:
            best_score = total_score
            best_po = po
    
    if best_score >= threshold:
        return best_po, best_score
    
    return None, None