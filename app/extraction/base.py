from abc import ABC, abstractmethod


class InvoiceExtractor(ABC):
    """Abstract base for invoice data extraction.

    All extractors must implement the extract() method which takes
    a path to a PDF invoice and returns structured data.
    """

    @abstractmethod
    def extract(self, pdf_path: str) -> dict:
        """Extract structured data from a PDF invoice.

        Args:
            pdf_path: Path to the PDF invoice file.

        Returns:
            A dict with extracted fields:
            {
                "invoice_number": str,
                "vendor_name": str,
                "date": str,
                "line_items": [
                    {"description": str, "quantity": float,
                     "unit_price": float, "total": float}
                ],
                "subtotal": float,
                "tax": float,
                "total": float,
                "po_number": str (if present)
            }
        """
        raise NotImplementedError
