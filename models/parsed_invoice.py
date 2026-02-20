class ParsedInvoice:
    def __init__(self, po_number=None, supplier=None, amount=None, status=None, date=None):
        self.po_number = po_number  # int, numeric portion extracted from PO string (e.g. 1234 from "PO-1234-AB")
        self.supplier = supplier    # str, vendor/company name
        self.amount = amount        # float
        self.status = status        # str, e.g. "pending", "complete", "in progress"
        self.date = date            # datetime, date invoice was issued