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

## Output Format
Return ONLY valid JSON with no additional text or markdown:
{
  "invoice_number": "string (required — the seller's invoice ID)",
  "vendor_name": "string — the company issuing/sending the invoice",
  "date": "YYYY-MM-DD — invoice issue date",
  "po_number": "string or null — the BUYER'S purchase order number referenced on this invoice",
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "line_items": [
    {
      "description": "string — part name or description",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ]
}

## Field Notes
- vendor_name: The vendor is the company ISSUING (sending) this invoice — the seller.
  Look for labels like "From:", "Sold by:", "Supplier:", "Bill From:", or a company name
  in the sender/supplier section. Do NOT use the buyer's name as the vendor. The buying
  company is ADS — any variation of this name (ADS, ADS Inc, Atlantic Diving Supply,
  ATLANTIC DIVING SUPPLY, ADS LLC, etc.) is the BUYER, not the vendor. Never use any
  ADS variation as the vendor_name.
- po_number: This is the BUYER'S internal purchase order number. All valid PO numbers
  in this system are EXACTLY 7 digits. This is a hard rule — if a number is not 7 digits,
  it is NOT a PO number regardless of its label.
  Scan the ENTIRE document before deciding. If you find multiple 7-digit candidates,
  prefer the one with the highest-priority label below.
  Known labels for the buyer's PO number, from most to least common:
    "P.O. Number", "Customer PO", "Customer PO No.", "Customer PO #", "Your Order",
    "Your Reference", "PO Number", "Purchase Order Number", "Purchase Order No.",
    "Customer P.O.", "Customer Order Number", "Customer PO Nbr", "PO No", "PO No.",
    "Purchase Order", "Customer Purchase Order", "Buyer Reference", "PO", "PO #",
    "P.O. No.", "Your Order No."
  Do NOT extract numbers under these labels — they are the SELLER'S internal references,
  not the buyer's PO: "Order Number", "Order No.", "Order #", "SO", "SO Number",
  "Sales Order", "Sales Order No.", "Invoice No.", "Invoice Number", "Reference No."
  If a document has multiple valid 7-digit PO numbers under different labels, return the
  one with the highest-priority label from the list above.
- invoice_number: Look for "Invoice #", "Invoice No.", "Invoice Number", "Inv #".
- date: Use the invoice issue date (not payment due date). Convert to YYYY-MM-DD format.
- All monetary values must be numbers (not strings). Remove currency symbols and commas.
- If a field is not found in the document, use null.
- If there are no line items, return an empty list for "line_items".
- Do not invent or infer values that are not clearly present in the text.\
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

    def extract_data(self, invoice_json: dict) -> dict:
        """Extract invoice data and return as a dict without saving to the database."""
        user_prompt = self._build_multi_user_prompt(invoice_json)
        raw_response = self._call_model(user_prompt)
        invoices = self._parse_multi_response(raw_response)
        return invoices[0]

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
                max_tokens=8192,
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
        # Strip Qwen3 thinking blocks before attempting JSON parse.
        # Handle both closed tags and unclosed tags (model hit token limit mid-thought).
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"<think>.*$", "", raw, flags=re.DOTALL).strip()

        if not raw:
            raise ValueError(
                "Model returned an empty response after stripping thinking blocks. "
                "The model likely hit the token limit during its thinking phase and "
                "never produced JSON output. Try increasing max_tokens or simplifying the input."
            )

        try:
            return json.loads(repair_json(raw))
        except (json.JSONDecodeError, ValueError):
            pass

        fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
        if fenced:
            try:
                return json.loads(repair_json(fenced.group(1)))
            except (json.JSONDecodeError, ValueError):
                pass

        brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace_match:
            try:
                return json.loads(repair_json(brace_match.group(0)))
            except (json.JSONDecodeError, ValueError):
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
