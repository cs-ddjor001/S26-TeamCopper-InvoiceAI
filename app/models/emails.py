from app.extensions import db

class Emails(db.Model):
    __tablename__ = "emails"

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), db.ForeignKey("email_addresses.email_address"), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String)
    data = db.Column(db.JSON)
