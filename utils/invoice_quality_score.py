def compute_invoice_quality(data: dict, raw_text: str | None = None) -> int:
    """
    Calculate a 0-100 invoice quality score based on the completeness of the 
    extracted fields of an invoice and the quality of the raw text extraction.

    Args: 
        data: the structured invoice dict after running the extraction and normalization.
        raw_text: the raw text extracted from the invoice PDF via pdfplumber, if it is given.

    Yields:
        An integer score between 0 and 100, inclusive, where 0 is the worst quality score 
        and 100 being the best.
    """
    invoice_quality_score = 100 # This is just the default to subtract from later.

    # First trying to see how good of quality is the text extraction itself, if we have it.
    if raw_text is not None:
        if len(raw_text) < 200:
            invoice_quality_score -= 15
        if raw_text.count("\n") < 3:
            invoice_quality_score -= 10
        if not any(ch.isdigit() for ch in raw_text):
            invoice_quality_score -= 20

    # Moving on to seeing how good of quality is the actual invoice fields extracted.
    # Essentially, were they found or not?
    if not data.get("po_number"):
        invoice_quality_score -= 30
    if not data.get("total"):
        invoice_quality_score -= 10
    if not data.get("date"):
        invoice_quality_score -= 8

    invoice_line_items = data.get("line_items", [])
    if not invoice_line_items:
        invoice_quality_score -= 30
        return max(invoice_quality_score, 0)
    for line_item in invoice_line_items:
        if not line_item.get("part_number") and not line_item.get("description"):
            invoice_quality_score -= 20
        if line_item.get("unit_price") in (None, ""):
            invoice_quality_score -= 10
        if line_item.get("quantity") in (None, ""):
            invoice_quality_score -= 8
        if line_item.get("total") in (None, ""):
            invoice_quality_score -= 8
    return max(invoice_quality_score, 0)



