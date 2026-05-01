from app.extensions import db

class Invoice_Line_Item(db.Model):
    __tablename__ = "invoice_line_items"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    line_num = db.Column(db.Integer, nullable=True)
    part_number = db.Column(db.String(100), nullable=True)
    part_description = db.Column(db.String(500), nullable=True)
    unit_of_measure = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    unit_price = db.Column(db.Float, nullable=True)
    amt_invoiced = db.Column(db.Float, nullable=True)
    clin = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Invoice_Line_Item invoice={self.invoice_id} line={self.line_num}>"