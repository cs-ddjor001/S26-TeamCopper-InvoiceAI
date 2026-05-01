import csv
import os
import re

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from app.extensions import db
from app.models.purchase_orders import Purchase_Order
from app.models.po_line_item import PO_Line_Item


CSV_FILES = [
    "data/ADS_POs_csvs/Invoice_PO_Data.csv",
    "data/ADS_POs_csvs/Invoice_PO_Data_2.csv",
]


def normalize_vendor(name):
    return re.sub(r"\s+", " ", name).strip() if name else None


def parse_date(value):
    if not value or not value.strip():
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_float(value):
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def parse_int(value):
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def load_purchase_orders(filepaths=None):
    if filepaths is None:
        filepaths = CSV_FILES

    po_cache = {po.po_number: po.id for po in Purchase_Order.query.all()}

    loaded_pos = 0
    loaded_lines = 0
    skipped_rows = 0

    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        print(f"Loading: {filepath}")

        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                po_number = parse_int(row.get("PO_NUMBER", ""))
                if po_number is None:
                    skipped_rows += 1
                    continue

                if po_number not in po_cache:
                    po = Purchase_Order(
                        po_number=po_number,
                        vendor_name=normalize_vendor(row.get("PO_VENDOR_NAME", "")),
                        vendor_id=parse_int(row.get("PO_VENDOR_ID", "")),
                        po_date=parse_date(row.get("PO_DATE", "")),
                        po_status=row.get("PO_STATUS", "").strip() or None,
                        buyer_name=row.get("PO_BUYER_NAME", "").strip() or None,
                    )
                    db.session.add(po)
                    db.session.flush()
                    po_cache[po_number] = po.id
                    loaded_pos += 1

                line_item = PO_Line_Item(
                    po_id=po_cache[po_number],
                    line_num=parse_int(row.get("PO_LINE_NUM", "")),
                    part_number=row.get("PART_NUMBER", "").strip() or None,
                    part_description=row.get("PART_DESCRIPTION", "").strip() or None,
                    unit_of_measure=row.get("UNIT_OF_MEASURE", "").strip() or None,
                    qty_ordered=parse_float(row.get("PO_QTY_ORDERED", "")),
                    qty_delivered=parse_float(row.get("PO_QTY_DELIVERED", "")),
                    qty_cancelled=parse_float(row.get("PO_QTY_CANCEL", "")),
                    unit_price=parse_float(row.get("PO_UNIT_PRICE", "")),
                    amt_invoiced=parse_float(row.get("PO_AMT_INVOICED", "")),
                    line_status=row.get("PO_LINE_LOCATION_STATUS", "").strip() or None,
                    clin=row.get("CLIN", "").strip() or None,
                )
                db.session.add(line_item)
                loaded_lines += 1

    db.session.commit()
    print(
        f"Done — PO headers: {loaded_pos}, "
        f"line items: {loaded_lines}, "
        f"rows skipped: {skipped_rows}"
    )


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        load_purchase_orders()
