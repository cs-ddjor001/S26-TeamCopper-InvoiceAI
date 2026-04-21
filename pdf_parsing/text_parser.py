from pathlib import Path
from extraction.pdfplumber_extractor import extract_invoice_pdf as extract_pdf_json
from extraction.ai_extractor import AIExtractor
from utils.invoice_quality_score import compute_invoice_quality


def _resolve_pdf_path(filepath):
    path = Path(filepath)
    if path.is_file():
        return path

    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "data" / "uploads" / path.name,
        project_root / "data" / path.name,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"PDF not found: {filepath}")


def parse_invoice_pdf(filepath):
    """Extract text from a PDF with pdfplumber, then use Qwen to structure it.

    Returns:
        Dict with structured invoice fields (invoice_number, vendor_name, date,
        po_number, subtotal, tax, total, line_items) ready for InvoiceValidator.

    Raises:
        FileNotFoundError: If the PDF cannot be found.
        ConnectionError: If llama-server is not reachable.
    """
    resolved_path = _resolve_pdf_path(filepath)
    invoice_json = extract_pdf_json(str(resolved_path))

    raw_text = "\n\n".join(p["text"] for p in invoice_json["pages"]).strip()
    if not raw_text:
        raise ValueError(
            f"No text could be extracted from {resolved_path.name}. "
            "The PDF may be image-based (scanned). Only text-based PDFs are supported."
        )

    data = AIExtractor().extract_data(invoice_json)

    invoice_quality_score = compute_invoice_quality(data, raw_text)
    data["invoice_quality_score"] = invoice_quality_score

    return data