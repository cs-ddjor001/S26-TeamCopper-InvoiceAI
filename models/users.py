from extensions import db


class Users(db.Model):
    username = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(30), nullable=False)
    display_name = db.Column(db.String(30))
    active = db.Column(db.Boolean, nullable=False)
    creation_time = db.Column(db.Time, nullable=False)
    deactivation_time = db.Column(db.Time)
    enabled_in_queue = db.Column(db.Boolean, nullable=False)
