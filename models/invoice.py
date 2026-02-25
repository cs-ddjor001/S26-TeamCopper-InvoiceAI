from extensions import db


class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    vendor = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")
    date_issued = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Invoice {self.id}>"