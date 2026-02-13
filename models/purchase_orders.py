from extensions import db
from sqlalchemy import ForeignKeyConstraint

class Purchase_Order(db.Model):
    id = db.Column(db.Integer, primaryKey=True)
    vendor = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_issued = db.Column(db.DateTime, nullable=False)
    ForeignKeyConstraint(["vendor"], ["vendors.id"])

    def __repr__(self):
        return f'Purchase order {self.id}'