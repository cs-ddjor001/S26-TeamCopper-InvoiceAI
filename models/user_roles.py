from extensions import db

class User_Roles(db.Model):
    __tablename__ = "user_roles"

    username = db.Column(db.String(20), db.ForeignKey("users.username"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), primary_key=True)
