from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
import re
from datetime import datetime

class ValidationIssue(BaseModel):
    field: str
    severity: str #warning/error
    message: str
    # original_value = Optional[str] = None

#sale of item blah blah
class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None

    #_issues: List[ValidationIssue] = []

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

    # validates the organized raw text from AI, and then after validation send to database
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    date: Optional[str] = None
    line_items: list[LineItem] = []
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    po_number: Optional[str] = None

    @field_validator("po_number", mode="before")
    @classmethod
    def validate_po_num(cls,v):
        if v is None:
            raise ValueError("PO Number is not here")
        #convert to string if is a number
        po_str = str(v).strip()

        #removing prefixes
        for prefix in ['PO-', 'PO#', 'PO ', 'P.O. ' 'PO']:
            if po_str.upper().startswith(prefix.upper()):
                po_str = po_str[len(prefix):].strip()
        
        #only da digits
        digits = re.sub(r'\D', '', po_str)

        #common pattern is for po#'s to be 7 digits
        if len(digits) != 7:
            raise ValueError(f"PO Number must be 7 digits, received {len(digits)} digits.")
        
        return digits
    
    @field_validator("vendor_name")
    @classmethod
    def validate_vendor_name(cls, v: Optional[str]) -> str:
        if v is None:
            raise ValueError("Vendor Name is required")
        
        cleaned = v.strip()

        if not cleaned:
            raise ValueError("Vendor Name is missing")
        
        if len(cleaned)< 2:
            raise ValueError("Vendor name is too short (min 2 characters)")
        
        return cleaned
    
    @field_validator("total", mode="before")
    @classmethod
    def validate_total(cls, v):
        if v is None:
            raise ValueError("Total amount required")
        
        #parse
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
                raise ValueError(f"Invalid total amount format: {v}")
            
        raise ValueError(f"Total must be a number or a string, received {type(v)}")
    #validation_issues: List[ValidationIssue] = []

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        if not v:
            return None

        # Already correct format
        if isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            #make sure it's reasonable
            try: 
                parsed = datetime.strptime(v, "%Y-%m-%d")
                #flag if outside resonable range (OCR) 
                if not (2000 <= parsed.year <= 2030):
                    return None #or raise valueerror with issue tracking
                return v
            except ValueError:
                return None

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
                parsed = datetime.strptime(v,fmt)
                #validate year
                if not (2000 <= parsed.year <= 2030):
                    return None #or raise valueerror with issue tracking
                return parsed.strftime("%Y-%m-%d")
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