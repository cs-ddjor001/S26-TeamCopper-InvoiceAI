from models.purchase_orders import Purchase_Order


def match_invoice(invoice):
    po_and_score = {}

    results = Purchase_Order.query.all()
    for row in results:
        score = 0
        if invoice.po_number == row.po_number:
            score = score+50
        if invoice.vendor == row.vendor:
            score = score+20
        if invoice.amount == row.amount:
            score = score+15
        if invoice.date_issued == row.date_issued:
            score = score+15

        po_and_score.update({row:score})
    
    return po_and_score
