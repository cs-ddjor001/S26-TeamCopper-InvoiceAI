from app import app
from po_matching.run_ai_matching import run_ai_matching

if __name__ == "__main__":
    with app.app_context():
        run_ai_matching()
