class ParsedInvoice:
    def __init__(self, po_number=None, supplier=None, amount=None, status=None, date=None):
        self.po_number = po_number  # string like "PO-1234-AB"
        self.supplier = supplier    # vendor name (string)
        self.amount = amount        # float
        self.status = status        # string
        self.date = date            # datetime