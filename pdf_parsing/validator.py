from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
import re
from datetime import datetime


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict) -> dict:
        # AI sometimes uses 'amount' or 'extended_amount' instead of 'total'
        if "total" not in data:
            data["total"] = (
                data.get("amount")
                or data.get("extended_amount")
                or data.get("line_total")
                or data.get("ext_price")
            )
        return data

    @field_validator("unit_price", "total", mode="before")
    @classmethod
    def parse_currency(cls, v):
        if v is None: 
            return None
        if isinstance(v, (dict, list)):
            return None
        
        if isinstance(v, (int, float)):
            return float(v)
        
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            # If the AI misread a comma thousands separator as a period (e.g. "22.810.20"),
            # strip all but the last period so it parses correctly.
            if cleaned.count(".") > 1:
                parts = cleaned.rsplit(".", 1)
                cleaned = parts[0].replace(".", "") + "." + parts[1]
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None


class InvoiceValidator(BaseModel):

    # Validates the raw AI-generated invoice JSON and exposes clean, typed fields
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    date: Optional[str] = None
    line_items: list[LineItem] = []
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    po_number: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict) -> dict:
        # Vendor name fallbacks
        if not data.get("vendor_name"):
            data["vendor_name"] = (
                data.get("supplier")
                or data.get("vendor")
                or data.get("company_name")
                or data.get("vendor_company")
                or data.get("bill_from")
                or data.get("seller")
                or data.get("ship_from")
                or data.get("remit_to")
                or data.get("sold_by")
                or data.get("issued_by")
            )
        if data.get("vendor_name") is None:
            import logging
            logging.warning(
                f"vendor_name missing. Available keys: {list(data.keys())}"
            )

        # Date fallbacks
        if not data.get("date"):
            data["date"] = (
                data.get("invoice_date")
                or data.get("issue_date")
                or data.get("date_issued")
            )

        # PO number fallbacks — covers all common label variations the model may use
        if not data.get("po_number"):
            data["po_number"] = (
                data.get("customer_po")
                or data.get("customer_po_number")
                or data.get("customer_po_nbr")
                or data.get("customer_po_no")
                or data.get("cust_po")
                or data.get("purchase_order")
                or data.get("purchase_order_number")
                or data.get("purchase_order_no")
                or data.get("po_num")
                or data.get("po_no")
                or data.get("po_ref")
                or data.get("buyer_reference")
                or data.get("buyer_po")
                or data.get("your_reference")
                or data.get("your_ref")
                or data.get("customer_reference")
                or data.get("customer_ref")
                or data.get("cust_ref")
                or data.get("client_reference")
                or data.get("client_ref")
                or data.get("client_po")
                or data.get("order_reference")
                or data.get("order_ref")
                or data.get("order_number")
                or data.get("order_no")
                or data.get("reference_number")
                or data.get("reference")
                or data.get("contract_number")
                or data.get("contract_no")
                or data.get("job_number")
                or data.get("job_no")
            )
        if isinstance(data.get("po_number"), dict):
            po_dict = data["po_number"] 
            for key in (
                "customer_po",
                "po_number",
                "po_no",
                "po_num",
                "order_number",
                "reference",
            ):
                if key in po_dict and po_dict[key]:
                    data["po_number"] = po_dict[key]
                    break
            else:
                data["po_number"] = None

        # Total fallbacks
        if not data.get("total"):
            data["total"] = (
                data.get("total_amount_due")
                or data.get("amount_due")
                or data.get("total_due")
                or data.get("invoice_total")
                or data.get("balance_due")
                or data.get("grand_total")
                or data.get("net_due")
            )

        # Making sure line_item key exists
        if "line_items" not in data or data["line_items"] is None:
            data["line_items"] = []

        cleaned_items = []
        for item in data.get("line_items", []):
            if not isinstance(item, dict):
                continue
            for key in ("unit_price", "total", "quantity"):
                if isinstance(item.get(key), dict):
                    item[key] = None
            cleaned_items.append(item)

        data["line_items"] = cleaned_items
        
        return data

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        if not v:
            return None
        # Already correct format
        if isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            return v
        # Try common formats the AI might return
        for fmt in (
            "%Y-%m-%d",
            "%d-%b-%Y",   # 10-FEB-2025
            "%m/%d/%Y",   # 2/8/2025 (US format, try before EU)
            "%d/%m/%Y",   # 10/02/2025
            "%B %d, %Y",  # August 29, 2024
            "%b %d, %Y",  # Aug 29, 2024
            "%d %B %Y",   # 29 August 2024
            "%Y/%m/%d",   # 2025/02/08
        ):
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
            except Exception:
                continue
        return None

    @field_validator("total", "subtotal", "tax", mode="before")
    @classmethod
    def validate_currency(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            if cleaned.count(".") > 1:
                parts = cleaned.rsplit(".", 1)
                cleaned = parts[0].replace(".", "") + "." + parts[1]
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @field_validator("vendor_name", "invoice_number")
    @classmethod
    def not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            return None
        return v.strip()

    # Convenience properties that map JSON fields to DB column names
    @property
    def supplier(self) -> Optional[str]:
        return self.vendor_name

    @property
    def amount(self) -> float:
        return self.total or 0.0

    @property
    def status(self) -> str:
        return "pending"

    @property
    def po_number_int(self) -> Optional[int]:
        if self.po_number:
            try:
                return int(str(self.po_number).strip())
            except ValueError:
                return None
        return None