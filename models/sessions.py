from sqlalchemy import ForeignKeyConstraint
from extensions import db


class Sessions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    created = db.Column(db.Time, nullable=False)
    expires = db.Column(db.Time, nullable=False)
    ForeignKeyConstraint(["username"], ["users.username"])
