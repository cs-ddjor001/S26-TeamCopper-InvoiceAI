from models.purchase_orders import Purchase_Order

# Again, this is based on my assumption, will change accordingly.

def match_invoice(parsed_invoice):
    if parsed_invoice.po_number:
        found_match = match_to_po_directly(parsed_invoice.po_number)
        if found_match:
            return found_match

    return match_by_other_fields(parsed_invoice)


def match_to_po_directly(po_number):
    return Purchase_Order.query.filter_by(id=po_number).first()


def match_by_other_fields(parsed_invoice):
    return Purchase_Order.query.filter_by(
        date_issued=parsed_invoice.date,
        vendor=parsed_invoice.vendor,
        amount=parsed_invoice.amount
    ).first()
