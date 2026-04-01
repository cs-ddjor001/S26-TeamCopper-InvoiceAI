from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
import re
from datetime import datetime


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

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
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            # If the AI misread a comma thousands separator as a period (e.g. "22.810.20"),
            # strip all but the last period so it parses correctly.
            if cleaned.count(".") > 1:
                parts = cleaned.rsplit(".", 1)
                cleaned = parts[0].replace(".", "") + "." + parts[1]
            return float(cleaned)
        return v


class InvoiceValidator(BaseModel):

    # Validates the raw AI-generated invoice JSON and exposes clean, typed fields
    invoice_number: str
    vendor_name: Optional[str] = None
    date: str
    line_items: list[LineItem]
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    po_number: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict) -> dict:
        # Vendor name fallbacks
        if "vendor_name" not in data:
            data["vendor_name"] = (
                data.get("supplier")
                or data.get("vendor")
                or data.get("company_name")
                or data.get("vendor_company")
                or data.get("bill_from")
                or data.get("seller")
                or data.get("ship_from")
            )
        if data.get("vendor_name") is None:
            import logging
            logging.warning(
                f"vendor_name missing. Available keys: {list(data.keys())}"
            )

        # Date fallbacks
        if "date" not in data:
            data["date"] = (
                data.get("invoice_date")
                or data.get("issue_date")
                or data.get("date_issued")
            )

        # PO number fallbacks
        if "po_number" not in data:
            data["po_number"] = (
                data.get("customer_po")
                or data.get("purchase_order")
                or data.get("po_num")
                or data.get("buyer_reference")
                or data.get("your_reference")
            )

        return data

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if v is None:
            raise ValueError("Date is required")
        # Already correct format
        if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
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
            except ValueError:
                continue
        raise ValueError(f"Unrecognised date format: '{v}'")

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
                raise ValueError(f"Invalid currency value: '{v}'")
        return None

    @field_validator("vendor_name", "invoice_number")
    @classmethod
    def not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()

    # Convenience properties that map JSON fields to DB column names
    @property
    def supplier(self) -> str:
        return self.vendor_name

    @property
    def amount(self) -> float:
        return self.total or 0.0

    @property
    def status(self) -> str:
        return "pending"

    @property
    def po_number_int(self) -> Optional[int]:
        if self.po_number and self.po_number.strip():
            try:
                return int(self.po_number.strip())
            except ValueError:
                return None
        return None