from models.purchase_orders import Purchase_Order


def match_invoice(invoice):
    if invoice.po_number:
        po = match_to_po_directly(invoice.po_number)
        if po:
            return po, 100

    po = match_by_fields(invoice)
    if po:
        return po, 100

    return None, None


def match_to_po_directly(po_number):
    return Purchase_Order.query.filter_by(po_number=po_number).first()


def match_by_fields(invoice):
    return Purchase_Order.query.filter_by(
        vendor=invoice.vendor,
        amount=invoice.amount,
        date_issued=invoice.date_issued,
    ).first()
