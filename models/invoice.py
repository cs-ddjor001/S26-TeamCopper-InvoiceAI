from extensions import db
from sqlalchemy import ForeignKeyConstraint

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.Integer, nullable=False)
    vendor = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")
    ForeignKeyConstraint(['po_number'],['purchase_orders.id'])
    ForeignKeyConstraint(['vendor'], ['vendors.id'])

    def __repr__(self):
        return f"<Invoice {self.po_number}>"
