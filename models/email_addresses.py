from extensions import db

class Email_Addresses(db.Model):
    __tablename__ = "email_addresses"

    email_address = db.Column(db.String(50), primary_key=True)
    vendor = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)

    def __repr__(self):
        return f"Email address: {self.email_address}"
