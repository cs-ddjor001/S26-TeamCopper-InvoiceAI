from extensions import db


class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.Integer, nullable=True)
    matched_po_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    vendor_name = db.Column(db.String(200), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default="pending")
    date_issued = db.Column(db.DateTime, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Invoice {self.id}>"
