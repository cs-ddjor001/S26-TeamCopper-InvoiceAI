"""Test vision-based invoice extraction against a running llama-server.

Usage:
    python scripts/test_extraction.py data/ADS_Invoice_PDFs/some_invoice.pdf

Requires llama-server running at localhost:8080 (or set LLAMA_SERVER_URL).
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extraction import VisionExtractor


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_extraction.py <path-to-invoice.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extractor = VisionExtractor()

    print(f"Extracting data from: {pdf_path}")
    print(f"Using server at: {extractor.base_url}")
    print("-" * 50)

    app = create_app()
    try:
        with app.app_context():
            result = extractor.extract(pdf_path)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Parse error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
