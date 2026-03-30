from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from app import app
from extensions import db


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(label)
    subprocess.run(command, cwd=cwd, check=True)


def initialize_database() -> None:
    with app.app_context():
        db.create_all()


def wipe_data_directory(data_dir: Path) -> None:
    if not data_dir.exists():
        return

    for item in data_dir.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def main() -> int:

    root = Path(__file__).resolve().parent
    data_dir = root / "data"
    db_path = root / "app.db"

    print("=== Invoice Setup ===")

    wipe_data_directory(data_dir)
    print("Cleared data directory")


    if db_path.exists():
        db_path.unlink()
        print("Removed app.db")
    else:
        print("app.db not found, skipping reset")

    python = sys.executable

    print("[0/4] Initializing database schema...")
    initialize_database()

    run_step("[1/4] Generating purchase orders CSV...", [python, "seeders/purchase_order_seeder.py"], root)
    run_step("[2/4] Loading purchase orders into database...", [python, "seeders/load_po_csv.py"], root)
    run_step("[3/4] Generating invoice PDFs...", [python, "seeders/invoice_pdf_seeder.py"], root)

    print("[4/4] Parsing invoice PDFs...")
    for pdf_path in sorted(data_dir.glob("sample_*.pdf")):
        subprocess.run([python, "parse_pdf.py", str(pdf_path)], cwd=root, check=True)

    print("\nDone. Start the app with: python app.py")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\nSetup failed while running: {' '.join(exc.cmd)}", file=sys.stderr)
        raise SystemExit(exc.returncode)
