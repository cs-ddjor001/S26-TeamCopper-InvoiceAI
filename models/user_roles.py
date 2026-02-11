from sqlalchemy import ForeignKeyConstraint
from extensions import db


class User_Roles(db.Model):
    username = db.Column(db.String(20), primary_key=True)
    role_id = db.Column(db.Integer, primary_key=True)
    ForeignKeyConstraint(["role_id"], ["roles.id"])
