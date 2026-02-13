from extensions import db
from sqlalchemy import ForeignKeyConstraint

class Email_Addresses(db.Model):
    email_address = db.Column(db.String(50), primary_key=True)
    vendor = db.Column(db.Integer, nullable=False)
    ForeignKeyConstraint(["vendor"], ["vendors.id"])

    def __repr__(self):
        return f'Email address: {self.email_address}'
