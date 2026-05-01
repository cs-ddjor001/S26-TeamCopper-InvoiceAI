import csv
import os
import re

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.extensions import db
from app.models.vendors import Vendors

CSV_FILES = [
    "data/ADS_POs_csvs/Invoice_PO_Data.csv",
    "data/ADS_POs_csvs/Invoice_PO_Data_2.csv",
]


def normalize_vendor(name):
    return re.sub(r"\s+", " ", name).strip() if name else None


def load_vendors(filepaths=None):
    if filepaths is None:
        filepaths = CSV_FILES

    vendor_cache = {v.id for v in Vendors.query.all()}

    loaded = 0
    skipped = 0

    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        print(f"Loading: {filepath}")

        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_id = row.get("PO_VENDOR_ID", "").strip()
                vendor_name = normalize_vendor(row.get("PO_VENDOR_NAME", ""))

                if not vendor_id or not vendor_name:
                    skipped += 1
                    continue

                vendor_id = int(vendor_id)

                if vendor_id not in vendor_cache:
                    vendor = Vendors(id=vendor_id, name=vendor_name)
                    db.session.add(vendor)
                    vendor_cache.add(vendor_id)
                    loaded += 1

    db.session.commit()
    print(f"Done — vendors loaded: {loaded}, rows skipped: {skipped}")


if __name__ == "__main__":
    from app import create_app
    from app.data_loaders.vendor_assignment import assign_vendors_to_users
    app = create_app()
    with app.app_context():
        db.create_all()
        load_vendors()
        print("Starting vendor assignment...")
        assign_vendors_to_users()
