from extensions import db

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), nullable=False)
    supplier = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")

    def __repr__(self):
        return f"<Invoice {self.po_number}>"
