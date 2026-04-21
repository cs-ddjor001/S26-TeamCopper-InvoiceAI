import datetime
import json
import os
import re

from openai import APIConnectionError, OpenAI
from json_repair import repair_json

from pdf_parsing.db_writer import save_parsed_invoice


DEFAULT_BASE_URL = os.environ.get("LLAMA_SERVER_URL", "http://localhost:8080/v1")
DEFAULT_MODEL = "qwen"
DEFAULT_OUTPUT_DIR = "./data/json_output"


SYSTEM_PROMPT = """\
You are an invoice data extraction assistant. You will be given JSON extracted
from a PDF invoice by pdfplumber. The JSON contains page text and tables.
Extract the invoice fields and return ONLY valid JSON with no additional text,
no markdown fences, and no explanation.

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

"vendor_name": The company or person sending/issuing the invoice (the seller or
supplier). Look for labels like: Vendor, Supplier, From, Bill From, Remit To,
Sold By, Seller, Ship From, Company Name. Do NOT use the buyer/customer name.
If you find a vendor named ADS, ignore it and keep looking.

"po_number": The purchase order reference number. This field may be labeled on
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


class AIExtractor:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.client = OpenAI(base_url=self.base_url, api_key="not-needed")

        configured_model = model or os.environ.get("LLAMA_MODEL")
        self.model = self._resolve_model_id(configured_model)

    @staticmethod
    def _find_model_match(requested: str, model_ids: list[str]) -> str | None:
        requested_norm = requested.strip().lower()
        for model_id in model_ids:
            if model_id.lower() == requested_norm:
                return model_id

        for model_id in model_ids:
            model_norm = model_id.lower()
            if requested_norm in model_norm or model_norm in requested_norm:
                return model_id

        return None

    def _resolve_model_id(self, configured_model: str | None) -> str:
        fallback_model = configured_model or DEFAULT_MODEL

        try:
            models = self.client.models.list()
        except Exception:
            return fallback_model

        model_ids = [m.id for m in getattr(models, "data", []) if getattr(m, "id", None)]
        if not model_ids:
            return fallback_model

        if configured_model:
            matched = self._find_model_match(configured_model, model_ids)
            if matched:
                return matched

            available = ", ".join(model_ids)
            raise ValueError(
                f"Configured model '{configured_model}' is not available at {self.base_url}. "
                f"Available models: {available}."
            )

        return self._find_model_match("qwen", model_ids) or model_ids[0]

    def extract(self, invoice_json: dict, source_name: str | None = None) -> dict:
        print("Extracting invoice data using AIExtractor extract method...")
        invoices = self.extract_many(invoice_json, source_name=source_name)
        return invoices[0]

    def extract_many(
        self, invoice_json: dict, source_name: str | None = None
    ) -> list[dict]:
        print("Extracting invoice data using AIExtractor extract_many method...")
        if not isinstance(invoice_json, dict):
            raise ValueError("Expected invoice_json to be a dictionary.")

        source_name = source_name or invoice_json.get("file") or "invoice_json"
        user_prompt = self._build_multi_user_prompt(invoice_json)
        raw_response = self._call_model(user_prompt)
        invoices = self._parse_multi_response(raw_response)

        saved: list[dict] = []
        for index, data in enumerate(invoices, start=1):
            suffix = f"-part{index}" if len(invoices) > 1 else ""
            self._save_json(data, f"{source_name}{suffix}")
            invoice = save_parsed_invoice(data)
            data["_invoice_id"] = invoice.id
            saved.append(data)

        return saved

    def _build_user_prompt(self, invoice_json: dict) -> str:
        payload = json.dumps(invoice_json, indent=2, ensure_ascii=False)
        if len(payload) > 20000:
            payload = payload[:20000] + "\n\n[TRUNCATED FOR CONTEXT]"

        return (
            "Extract invoice data from this pdfplumber JSON:\n\n"
            f"{payload}\n\n"
            "/no_think"
        )

    def _build_multi_user_prompt(self, invoice_json: dict) -> str:
        payload = json.dumps(invoice_json, indent=2, ensure_ascii=False)
        if len(payload) > 20000:
            payload = payload[:20000] + "\n\n[TRUNCATED FOR CONTEXT]"

        return (
            "Extract ALL invoices present in this pdfplumber JSON. "
            "If the PDF contains multiple invoices, return one object per invoice. "
            "Return only JSON in this exact shape:\n"
            "{\n"
            '  "invoices": [\n'
            "    {\n"
            '      "invoice_number": "string or null",\n'
            '      "vendor_name": "string or null",\n'
            '      "date": "YYYY-MM-DD or null",\n'
            '      "line_items": [],\n'
            '      "subtotal": number or null,\n'
            '      "tax": number or null,\n'
            '      "total": number or null,\n'
            '      "po_number": "string or null"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "If only one invoice is present, return one item in the invoices array.\n\n"
            f"{payload}\n\n"
            "/no_think"
        )

    def _save_json(self, data: dict, source_name: str) -> str:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(source_name))[0]
        invoice_number = data.get("invoice_number")

        if invoice_number:
            filename = f"{invoice_number}.json"
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.json"

        filepath = os.path.join(DEFAULT_OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return filepath

    def _call_model(self, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
        except APIConnectionError:
            raise ConnectionError(
                f"Cannot connect to llama-server at {self.base_url}. "
                "Make sure llama-server is running."
            )

        raw_response = response.choices[0].message.content or ""
        if not raw_response.strip():
            raise ValueError(
                "Model returned an empty response. Check that llama-server is "
                f"running the expected model at {self.base_url}, that LLAMA_MODEL "
                "matches the loaded model."
            )

        return raw_response

    @staticmethod
    def _parse_response(raw: str) -> dict:
        if not raw or not raw.strip():
            raise ValueError(
                "Model returned no text content to parse as JSON. Verify the model "
                "is producing a response and try again."
            )

        try:
            repaired = repair_json(raw)
            repaired = repair_json(repaired)
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
        if fenced:
            try:
                repaired = repair_json(fenced.group(1))
                repaired = repair_json(repaired)
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

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

    def _parse_multi_response(self, raw: str) -> list[dict]:
        parsed = self._parse_response(raw)

        if isinstance(parsed, dict) and isinstance(parsed.get("invoices"), list):
            invoices = [item for item in parsed["invoices"] if isinstance(item, dict)]
            if not invoices:
                raise ValueError("Model returned an empty invoices list.")
            return invoices

        if isinstance(parsed, list):
            invoices = [item for item in parsed if isinstance(item, dict)]
            if not invoices:
                raise ValueError("Model returned a list with no invoice objects.")
            return invoices

        if isinstance(parsed, dict):
            return [parsed]

        raise ValueError("Model response was not a valid invoice object/list.")


def extract_invoice_json(invoice_json: dict, source_name: str | None = None) -> dict:
    return AIExtractor().extract(invoice_json, source_name=source_name)


def extract_invoices_json(
    invoice_json: dict, source_name: str | None = None
) -> list[dict]:
    return AIExtractor().extract_many(invoice_json, source_name=source_name)
