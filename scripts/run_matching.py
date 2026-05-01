"""Run deterministic invoice-to-PO matching on all unmatched invoices."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.matching.run_matching import run_matching

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_matching()
