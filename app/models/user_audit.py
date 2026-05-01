from app.extensions import db

class User_Audit(db.Model):
    __tablename__ = "user_audit"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey("users.username"))
    invoice = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    time = db.Column(db.Time, nullable=False)
