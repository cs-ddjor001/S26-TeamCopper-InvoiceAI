from extensions import db


class PO_Line_Item(db.Model):
    __tablename__ = "po_line_items"

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    line_num = db.Column(db.Integer, nullable=True)
    part_number = db.Column(db.String(100), nullable=True)
    part_description = db.Column(db.String(500), nullable=True)
    unit_of_measure = db.Column(db.String(50), nullable=True)
    qty_ordered = db.Column(db.Float, nullable=True)
    qty_delivered = db.Column(db.Float, nullable=True)
    qty_cancelled = db.Column(db.Float, nullable=True)
    unit_price = db.Column(db.Float, nullable=True)
    amt_invoiced = db.Column(db.Float, nullable=True)
    line_status = db.Column(db.String(50), nullable=True)
    clin = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<PO_Line_Item po={self.po_id} line={self.line_num}>"
