from app.extensions import db

class Match(db.Model):
    __tablename__ = "match"

    match_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    po_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    confidence_score = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Match {self.match_id}>"
