from extensions import db

class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    vendor = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")

    def __repr__(self):
        return f"<Invoice {self.po_number}>"
