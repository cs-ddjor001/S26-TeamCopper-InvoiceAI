import os
import shutil

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Invoice
from app.extraction.ai_extractor import extract_invoices_json
from app.extraction.vision_extractor import VisionExtractor
from app.extraction.pdfplumber_extractor import extract_invoice_pdf
from app.matching.run_matching import run_matching
from app.matching.run_ai_matching import run_ai_matching

invoice_bp = Blueprint("invoice", __name__)


def _is_text_based_pdf(extracted_pdf: dict) -> bool:
    pages = extracted_pdf.get("pages", []) if isinstance(extracted_pdf, dict) else []
    for page in pages:
        text = page.get("text", "") if isinstance(page, dict) else ""
        if text and text.strip():
            return True
    return False


@invoice_bp.route("/run-matching", methods=["POST"])
def trigger_matching():
    session_user = session.get("username")
    run_matching()
    return redirect(f"/ap/{session_user}" if session_user else url_for("ap.ap"))


@invoice_bp.route("/run-ai-matching", methods=["POST"])
def trigger_ai_matching():
    session_user = session.get("username")
    run_ai_matching()
    return redirect(f"/ap/{session_user}" if session_user else url_for("ap.ap"))


@invoice_bp.route("/invoice-pdf/<int:invoice_id>")
def get_invoice_pdf(invoice_id):
    project_root = current_app.config["PROJECT_ROOT"]
    directory = os.path.join(project_root, "data")
    filename = f"sample_{invoice_id}.pdf"

    if not os.path.exists(os.path.join(directory, filename)):
        return "", 404

    return send_from_directory(directory, filename)


@invoice_bp.route("/upload-invoice", methods=["GET", "POST"])
def upload_invoice():
    session_user = session.get("username")
    if not session_user:
        return redirect(url_for("auth.home"))

    if request.method == "GET":
        return redirect(f"/ap/{session_user}")

    files = request.files.getlist("invoice_pdf")
    if not files or all(f.filename == "" for f in files):
        return redirect(f"/ap/{session_user}")

    project_root = current_app.config["PROJECT_ROOT"]
    upload_dir = os.path.join(project_root, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if not file or file.filename == "":
            continue
        if not file.filename.lower().endswith(".pdf"):
            continue

        filename = secure_filename(file.filename)
        pdf_path = os.path.join(upload_dir, filename)
        file.save(pdf_path)

        try:
            pdf_json = extract_invoice_pdf(pdf_path)

            if _is_text_based_pdf(pdf_json):
                results = extract_invoices_json(pdf_json, source_name=filename)
            else:
                results = [VisionExtractor().extract(pdf_path)]

            for result in results:
                invoice_id = result.get("_invoice_id")
                if invoice_id:
                    dest = os.path.join(project_root, "data", f"sample_{invoice_id}.pdf")
                    shutil.copy(pdf_path, dest)
                    invoice = Invoice.query.get(invoice_id)
                    if invoice:
                        invoice.uploaded_by = session_user
                        db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Invoice extraction failed for {filename}: {e}")
            flash(f"Could not process '{filename}': {e}", "error")

    return redirect(f"/ap/{session_user}")


@invoice_bp.route("/system-stats")
def system_stats():
    import psutil
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    stats = {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 1),
        "memory_total_gb": round(memory.total / (1024**3), 1),
    }
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            stats["gpu_percent"] = round(gpu.load * 100, 1)
            stats["gpu_memory_used_mb"] = round(gpu.memoryUsed)
            stats["gpu_memory_total_mb"] = round(gpu.memoryTotal)
            stats["gpu_name"] = gpu.name
        else:
            stats["gpu_percent"] = None
            stats["gpu_name"] = "No GPU detected"
    except ImportError:
        stats["gpu_percent"] = None
        stats["gpu_name"] = "GPUtil not installed"
    return jsonify(stats)
