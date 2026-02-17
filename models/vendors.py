from extensions import db

class Vendors(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'Vendor with name {self.name}'