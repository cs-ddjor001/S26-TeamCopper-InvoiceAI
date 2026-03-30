from extensions import db


class Purchase_Order(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.Integer, unique=True, nullable=False)
    vendor_name = db.Column(db.String(200), nullable=False)
    vendor_id = db.Column(db.Integer, nullable=True)
    po_date = db.Column(db.DateTime, nullable=True)
    po_status = db.Column(db.String(50), nullable=True)
    buyer_name = db.Column(db.String(200), nullable=True)

    line_items = db.relationship("PO_Line_Item", backref="purchase_order", lazy=True)

    def __repr__(self):
        return f"<PO {self.po_number}>"
