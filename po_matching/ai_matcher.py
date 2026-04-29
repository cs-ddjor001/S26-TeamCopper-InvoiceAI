import json
import os
import re
from openai import OpenAI, APIConnectionError
from json_repair import repair_json
from po_matching.fuzzy_matcher import get_top_candidates

MATCHING_SYSTEM_PROMPT = """\
You are an invoice-to-PO matching assistant. You will receive:
1. Extracted invoice data (from a parsed PDF)
2. A list of candidate Purchase Orders from our database

Your task: determine which PO best matches the invoice and calculate a
confidence score.

## Matching Rules (in priority order)

1. PO Number (50% of confidence score)
   - If the invoice contains a PO number, check for an exact match first.
   - If no exact match, consider close matches (e.g., formatting differences).
   - If the invoice has no PO number, this portion scores 0.

2. Part Number / Description (45% of confidence score)
   - Compare invoice line items against PO line items.
   - Match on part number first; if unavailable, match on part description.
   - A line item is considered matched if part similarity is 80% or higher
     AND the unit price is within tolerance.

3. Date (5% of confidence score)
   - Check if the invoice date is reasonably close to the PO date.
   - Exact date match scores full points; dates within 30 days score partial.

## Price Tolerance Rules
When comparing unit prices between invoice and PO line items:
- Standard tolerance: 2% difference allowed
- High-value items (PO unit price > $5,000): only 1% difference allowed
- Low-value items (PO unit price < $100): 5% difference allowed

## Confidence Score Calculation
Calculate the final confidence score as a number between 0 and 1 by combining
the weighted scores from each matching rule above.

Interpretation:
- Above 0.80: High confidence — likely an automatic match
- 0.50 to 0.80: Medium confidence — needs human review
- Below 0.50: Low confidence — likely not a match

## Output Format
Return ONLY valid JSON with no additional text:
{
  "matched_po_number": "string or null",
  "matched_po_line_num": number or null,
  "confidence_score": number between 0 and 1,
  "reasoning": "Brief explanation of the match decision",
  "field_matches": {
    "po_number": {"matched": true/false, "invoice_value": "...", "po_value": "..."},
    "part_number": {"matched": true/false, "invoice_value": "...", "po_value": "..."},
    "unit_price": {"within_tolerance": true/false, "invoice_value": 0, "po_value": 0, "difference_pct": 0},
    "vendor_name": {"matched": true/false, "invoice_value": "...", "po_value": "..."},
    "date": {"matched": true/false, "invoice_value": "...", "po_value": "..."}
  }
}

If no PO is a reasonable match, set matched_po_number to null and
confidence_score to 0.\
"""

DEFAULT_BASE_URL = os.environ.get("LLAMA_SERVER_URL", "http://localhost:8080/v1")


class AIMatcher:
    """Matches invoices to POs using the Qwen model via llama-server."""

    def __init__(self, base_url=None):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.client = OpenAI(base_url=self.base_url, api_key="not-needed")

    def match_invoice_to_po(self, invoice_data: dict, candidate_pos: list) -> dict:
        """Match extracted invoice data against candidate POs.

        Args:
            invoice_data: Structured invoice data dict.
            candidate_pos: List of candidate PO dicts from database query.

        Returns:
            Dict with matched_po_number, confidence_score, reasoning, field_matches.
        """
        user_prompt = self._build_matching_prompt(invoice_data, candidate_pos)

        try:
            response = self.client.chat.completions.create(
                model="qwen",
                messages=[
                    {"role": "system", "content": MATCHING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=8192,
                temperature=0.2,
            )
            raw = response.choices[0].message.content or ""
            return self._parse_response(raw)

        except APIConnectionError:
            raise ConnectionError(
                f"Cannot connect to llama-server at {self.base_url}. "
                "Make sure llama-server is running."
            )

    @staticmethod
    def _invoice_to_dict(invoice) -> dict:
        """Convert an Invoice DB model to a dict for the AI prompt."""
        return {
            "po_number": str(invoice.po_number) if invoice.po_number else None,
            "vendor_name": invoice.vendor_name,
            "amount": invoice.amount,
            "date_issued": (
                invoice.date_issued.strftime("%Y-%m-%d")
                if invoice.date_issued else None
            ),
            "line_items": [
                {
                    "line_num": li.line_num,
                    "part_number": li.part_number,
                    "part_description": li.part_description,
                    "quantity": li.quantity,
                    "unit_price": li.unit_price,
                    "amt_invoiced": li.amt_invoiced,
                    "clin": li.clin,
                }
                for li in (invoice.line_items or [])
            ],
        }

    @staticmethod
    def _po_to_dict(po) -> dict:
        """Convert a Purchase_Order DB model to a dict for the AI prompt."""
        return {
            "po_number": str(po.po_number),
            "vendor_name": po.vendor_name,
            "po_date": po.po_date.strftime("%Y-%m-%d") if po.po_date else None,
            "line_items": [
                {
                    "line_num": li.line_num,
                    "part_number": li.part_number,
                    "part_description": li.part_description,
                    "qty_ordered": li.qty_ordered,
                    "unit_price": li.unit_price,
                    "clin": li.clin,
                }
                for li in (po.line_items or [])
            ],
        }

    @staticmethod
    def _build_matching_prompt(invoice_data: dict, candidate_pos: list) -> str:
        return (
            "## Invoice Data\n"
            f"{json.dumps(invoice_data, indent=2)}\n\n"
            "## Candidate Purchase Orders\n"
            f"{json.dumps(candidate_pos, indent=2)}\n\n"
            "Match this invoice to the best PO and return the JSON result.\n\n/no_think"
        )

    @staticmethod
    def _parse_response(raw: str) -> dict:
        """Parse model response, handling common LLM output quirks."""
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

def match_invoice_ai(invoice, top_n=20):
    """Run AI matching for an Invoice DB object.

    Pre-filters to the top N candidates by fuzzy score before calling the model,
    keeping the prompt within the model's context window.

    Requires an active Flask app context (for DB queries).

    Returns:
        Tuple of (Purchase_Order, confidence_score_0_to_100) or (None, 0).
        Raises ConnectionError if llama-server is unreachable.
    """
    candidate_pos = get_top_candidates(invoice, n=top_n)
    if not candidate_pos:
        return None, 0

    ai = AIMatcher()
    invoice_dict = AIMatcher._invoice_to_dict(invoice)
    po_dicts = [AIMatcher._po_to_dict(po) for po in candidate_pos]

    result = ai.match_invoice_to_po(invoice_dict, po_dicts)

    matched_po_number = result.get("matched_po_number")
    confidence = result.get("confidence_score", 0)

    if not matched_po_number or confidence == 0:
        return None, 0

    matched_po = next(
        (po for po in candidate_pos if str(po.po_number) == str(matched_po_number)),
        None,
    )

    return matched_po, round(confidence * 100)
