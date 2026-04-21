"""Demo script to test invoice extraction with the Liquid AI vision model.

Usage:
    python test_extraction.py path/to/invoice.pdf
    python test_extraction.py data/sample_1.pdf

Requires llama-server running at localhost:8080 (or set LLAMA_SERVER_URL).
"""
import json
import sys

from app import app
from extraction import VisionExtractor


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_extraction.py <path-to-invoice.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extractor = VisionExtractor()

    print(f"Extracting data from: {pdf_path}")
    print(f"Using server at: {extractor.base_url}")
    print("-" * 50)

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
