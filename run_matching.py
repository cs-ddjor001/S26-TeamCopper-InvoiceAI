from app import app
from po_matching.run_matching import run_matching

if __name__ == "__main__":
    with app.app_context():
        run_matching()
