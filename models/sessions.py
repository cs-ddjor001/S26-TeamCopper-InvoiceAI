from extensions import db

class Sessions(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey("users.username"), nullable=False)
    created = db.Column(db.Time, nullable=False)
    expires = db.Column(db.Time, nullable=False)
