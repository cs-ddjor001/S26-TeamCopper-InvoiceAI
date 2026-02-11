from sqlalchemy import ForeignKeyConstraint
from extensions import db


class User_Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    invoice = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(200), nullable=False)
    time = db.Column(db.Time, nullable=False)
    ForeignKeyConstraint(["username"], ["users.username"])
    ForeignKeyConstraint(["invoice"], ["invoice.id"])
