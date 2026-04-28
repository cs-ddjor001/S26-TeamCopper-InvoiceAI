import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.vendors import Vendors

CSV_FILES = [
    "data/ADS_POs_csvs/Invoice_PO_Data.csv",
    "data/ADS_POs_csvs/Invoice_PO_Data_2.csv",
]


def normalize_vendor(name):
    return re.sub(r"\s+", " ", name).strip() if name else None


def load_vendors(filepaths=None):
    if filepaths is None:
        filepaths = CSV_FILES

    # Preload existing vendor IDs so no duplicates
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
                    vendor = Vendors(
                        id=vendor_id,
                        name=vendor_name,
                    )
                    db.session.add(vendor)
                    vendor_cache.add(vendor_id)
                    loaded += 1

    db.session.commit()
    print(f"Done — vendors loaded: {loaded}, rows skipped: {skipped}")


if __name__ == "__main__":
    from importlib.util import spec_from_file_location, module_from_spec

    assignment_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor_assignment.py")
    spec = spec_from_file_location("vendor_assignment", assignment_path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)

    with app.app_context():
        db.create_all()
        load_vendors()
        print("Starting vendor assignment...")
        mod.assign_vendors_to_users()