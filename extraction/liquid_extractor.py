import base64
from datetime import datetime
import json
import os
import re

import fitz  # PyMuPDF
from openai import OpenAI, APIConnectionError

from pdf_parsing.db_writer import save_parsed_invoice

from .base import InvoiceExtractor

from json_repair import repair_json

SYSTEM_PROMPT = """\
You are an invoice data extraction assistant. You will be given an image of an \
invoice. Extract the following fields and return ONLY valid JSON with no \
additional text, no markdown fences, and no explanation.

Required JSON structure:
{
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "date": "string in YYYY-MM-DD format or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ],
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "po_number": "string or null"
}

Field extraction guidance:

"vendor_name": The company or person sending/issuing the invoice (the seller or \
supplier). Look for labels like: Vendor, Supplier, From, Bill From, Remit To, \
Sold By, Seller, Ship From, Company Name. Do NOT use the buyer/customer name.

"po_number": The purchase order reference number. This field may be labeled on \
the invoice as any of the following — always map it to "po_number":
  PO Number, PO #, PO No, P.O. Number, P.O. #, Purchase Order, Purchase Order Number,
  Purchase Order No, Customer PO, Customer PO Number, Customer PO #, Customer PO No,
  Customer P.O., Cust PO, Cust PO #, Customer Reference, Customer Ref, Cust Ref,
  Your Reference, Your Ref, Order Reference, Order Ref, Reference Number, Ref No,
  Reference, Client Reference, Client Ref, Client PO, Buyer Reference, Buyer PO,
  Order Number, Order No, Contract Number, Contract No, Job Number, Job No.
If the invoice contains a value under ANY of these labels, place it in "po_number".
If multiple such labels are present, prefer the one most clearly labeled as a
purchase order number.

"total": The final amount due on the invoice. May be labeled: Total, Total Due,
Total Amount Due, Amount Due, Invoice Total, Balance Due, Grand Total, Net Due.

"date": The invoice issue date (not due date). May be labeled: Date, Invoice Date,
Date Issued, Issue Date.

Rules:
- All monetary values must be numbers (not strings). Remove currency symbols and commas.
- For line items, "total" is the line total (quantity × unit_price). It may be
  labeled: Total, Amount, Extended Amount, Line Total, Ext. Price.
- If a field is not present on the invoice, set it to null.
- If there are no line items, return an empty list for "line_items".
- Return ONLY the JSON object. No extra text.\
"""

USER_PROMPT = "Extract all invoice data from this image and return it as JSON."

DEFAULT_BASE_URL = "http://localhost:8080/v1"


class LiquidExtractor(InvoiceExtractor):
    """Extracts invoice data using the Liquid AI vision model (LFM2.5-VL)
    served locally via llama-server's OpenAI-compatible API."""

    def __init__(self, base_url: str | None = None, model: str = "liquid"):
        self.base_url = base_url or os.environ.get(
            "LLAMA_SERVER_URL", DEFAULT_BASE_URL
        )
        self.model = model
        self.client = OpenAI(base_url=self.base_url, api_key="not-needed")

    def extract(self, pdf_path: str) -> dict:
        """Extract structured invoice data from a PDF using the vision model.

        Args:
            pdf_path: Path to the PDF invoice file.

        Returns:
            Dict with extracted invoice fields.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ConnectionError: If the llama-server is not reachable.
            ValueError: If the model response cannot be parsed as JSON.
        """
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        image_b64 = self._pdf_to_base64_image(pdf_path) #pdf to image
        raw_response = self._call_model(image_b64) #image to ai model
        data = self._parse_response(raw_response)  #make response json
        self._save_json(data, pdf_path)
        invoice = save_parsed_invoice(data)
        data['_invoice_id'] = invoice.id
        return data                                

    def _save_json(self, data: dict, pdf_path: str): 
        """Save extracted JSON to file."""
        os.makedirs("./data/json_output", exist_ok=True)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        invoice_number = data.get("invoice_number")

        if invoice_number:
            filename = f"{invoice_number}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.json"

        filepath = os.path.join("./data/json_output", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4) 

    def _pdf_to_base64_image(self, pdf_path: str) -> str:
        """Convert the first page of a PDF to a base64-encoded PNG string."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        # Render at 2x resolution for better OCR quality
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        png_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(png_bytes).decode("utf-8")

    def _call_model(self, image_b64: str) -> str:
        """Send the image to the vision model and return the raw text response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                },
                            },
                            {
                                "type": "text",
                                "text": USER_PROMPT,
                            },
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=2048,
            )
        except APIConnectionError:
            raise ConnectionError(
                f"Cannot connect to llama-server at {self.base_url}. "
                "Make sure llama-server is running."
            )

        return response.choices[0].message.content

    @staticmethod
    def _parse_response(raw: str) -> dict:
        """Parse the model's response text into a structured dict.

        Handles cases where the model wraps JSON in markdown code fences
        or includes extra text around the JSON object.
        """

        # Try direct parse first
        try:
            repaired = repair_json(raw)
            repaired = repair_json(repaired)
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences: ```json ... ``` or ``` ... ```
        fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
        if fenced:
            try:
                repaired = repair_json(fenced.group(1))
                repaired = repair_json(repaired)
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace_match:
            try:
                repaired = repair_json(brace_match.group(0))
                repaired = repair_json(repaired)
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not parse model response as JSON. Raw response:\n{raw}"
        )
