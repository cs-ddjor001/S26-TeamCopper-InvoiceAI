from extensions import db

class Vendors(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('users.username'))

    def __repr__(self):
        return f'Vendor with name {self.name}'