from rapidfuzz import fuzz
from models.purchase_orders import Purchase_Order
import re

def normalize(text):
    if not text:
        return ""
    text = str(text).upper().strip()
    text = re.sub(r"[\s\-_:;,.]", "", text)
    return text
    
def fuzzy_score(a, b):
    if not a or not b:
        return 0
    return fuzz.ratio(normalize(a), normalize(b)) / 100.00

def price_within_tolerance(invoice_price, po_price):
    if invoice_price is None or po_price is None:
        return False
    
    tolerance = 0.02
    if po_price > 5000:
        tolerance = 0.01
    elif po_price < 100:
        tolerance = 0.05

    diff = abs(invoice_price - po_price) / po_price
    return diff <= tolerance

def match_by_fields_fuzzy(invoice, threshold=0.70):
    candidates = Purchase_Order.query.all()

    best_po = None
    best_score = 0

    for po in candidates:
        total_score = 0

        # PO number (50% weight)
        score_po = fuzzy_score(str(invoice.po_number or ""), str(po.po_number))
        total_score += 0.50 * score_po

        # vendor (15% weight)
        score_vendor = fuzzy_score(invoice.vendor_name, po.vendor_name)
        total_score += 0.15 * score_vendor

        # Part number and unit price matching (30% weight)
        score_line = 0
        for invoice_item in invoice.line_items:
            for po_item in po.line_items:
                score_part = max(fuzzy_score(invoice_item.part_number, po_item.part_number), 
                                        fuzzy_score(invoice_item.part_description, po_item.part_description))
                if score_part >= 0.80:
                    if price_within_tolerance(invoice_item.unit_price, po_item.unit_price):
                        score_line = max(score_line, score_part)
        total_score += 0.30 * score_line

        # Date (5% weight)
        score_date = 100 if invoice.date_issued == po.po_date else 0
        total_score += 0.05 * score_date

        if total_score > best_score:
            best_score = total_score
            best_po = po
    
    if best_score >= threshold:
        return best_po, best_score
    
    return None, None