from decimal import Decimal, InvalidOperation
from typing import Optional
from pydantic import BaseModel, field_validator
import re


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: str
    total: str


class InvoiceValidator(BaseModel):
 
# Validates the raw AI-generated invoice JSON and exposes clean, typed fields

    invoice_number: str
    vendor_name: str
    date: str
    line_items: list[LineItem]
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    po_number: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"Expected YYYY-MM-DD, got: '{v}'")
        return v

    @field_validator("total", "subtotal", "tax", mode="before")
    @classmethod
    def validate_currency(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Invalid currency value: '{v}'")

    @field_validator("vendor_name", "invoice_number")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
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