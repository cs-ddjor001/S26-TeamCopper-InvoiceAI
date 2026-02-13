from extensions import db
from sqlalchemy import ForeignKeyConstraint

class Emails(db.Model):
    id = db.Column(db.Integer, primaryKey=True)
    sender = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    # potentially very large, could use later if needed
    # body = db.Column(db.String)
    filepath = db.Column(db.String)
    data = db.Column(db.JSON)
    ForeignKeyConstraint(['sender'],['email_addresses.email_address'])