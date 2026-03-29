import csv
import os
import sys

# Add project root to path so imports resolve regardless of where script is run from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import app
from extensions import db
from models.vendors import Vendors
from models.purchase_orders import Purchase_Order


def load_purchase_orders(filepath="data/purchase_orders.csv"):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    loaded = 0
    skipped = 0

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            po_number = row["po_number"].strip()
            vendor_name = row["vendor"].strip()
            amount = float(row["amount"])
            date_issued = datetime.strptime(row["date_issued"].strip(), "%Y-%m-%d")

            # Skip if PO already exists
            if Purchase_Order.query.filter_by(po_number=po_number).first():
                skipped += 1
                continue

            vendor = Vendors.query.filter_by(name=vendor_name).first()
            if not vendor:
                vendor = Vendors(name=vendor_name)
                db.session.add(vendor)
                db.session.flush()

            po = Purchase_Order(
                po_number=po_number,
                vendor=vendor.id,
                amount=amount,
                date_issued=date_issued,
            )
            db.session.add(po)
            loaded += 1

    db.session.commit()
    print(f"Done — loaded: {loaded}, skipped (already exist): {skipped}")


if __name__ == "__main__":
    with app.app_context():
        load_purchase_orders()
