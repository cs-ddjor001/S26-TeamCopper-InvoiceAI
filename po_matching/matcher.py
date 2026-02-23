from models.purchase_orders import Purchase_Order
from models.vendors import Vendors


def match_invoice(parsed_invoice):
    if parsed_invoice.po_number:
        found_match = match_to_po_directly(parsed_invoice.po_number)
        if found_match:
            return found_match

    return match_by_fields(parsed_invoice)


def match_to_po_directly(po_number):
    return Purchase_Order.query.filter_by(po_number=po_number).first()


def match_by_fields(parsed_invoice):
    vendor = Vendors.query.filter_by(name=parsed_invoice.supplier).first()

    if not vendor:
        return None
    
    return Purchase_Order.query.filter_by(
        vendor = vendor.id,
        amount=parsed_invoice.amount,
        date_issued=parsed_invoice.date
    ).first()