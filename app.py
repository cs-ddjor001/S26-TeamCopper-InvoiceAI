from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    send_from_directory,
    request,
    flash,
    jsonify,
)
from datetime import date, datetime
import os
import shutil
from extensions import db

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "app.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "invoiceai-dev-key"  # Necessary for flash messages (show errors)

db.init_app(app)


def format_datetime(value, fmt="%m/%d/%Y"):
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(fmt)

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).strftime(fmt)

    if isinstance(value, str):
        for parse_fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, parse_fmt).strftime(fmt)
            except ValueError:
                continue

    return str(value)


app.jinja_env.filters["format_datetime"] = format_datetime

import models
from po_matching.run_matching import run_matching
from werkzeug.utils import secure_filename
from extraction.ai_extractor import extract_invoices_json
from extraction.vision_extractor import VisionExtractor
from extraction.pdfplumber_extractor import extract_invoice_pdf


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    invoices = models.Invoice.query.all()
    purchase_orders = models.Purchase_Order.query.all()
    pending_count = sum(1 for i in invoices if i.status != "complete")
    completed_count = sum(1 for i in invoices if i.status == "complete")
    total_value = sum(i.amount for i in invoices if i.amount)
    avg_value = total_value / len(invoices) if invoices else 0
    low_confidence = sum(
        1
        for i in invoices
        if i.confidence_score is not None and i.confidence_score < 50
    )
    med_confidence = sum(
        1
        for i in invoices
        if i.confidence_score is not None and 50 <= i.confidence_score < 80
    )
    high_confidence = sum(
        1
        for i in invoices
        if i.confidence_score is not None and i.confidence_score >= 80
    )
    vendor_names = sorted(set(i.vendor_name for i in invoices if i.vendor_name))
    vendor_count = len(vendor_names)
    return render_template(
        "dashboard.html",
        invoices=invoices,
        purchase_orders=purchase_orders,
        pending_count=pending_count,
        completed_count=completed_count,
        total_value=total_value,
        avg_value=avg_value,
        low_confidence=low_confidence,
        med_confidence=med_confidence,
        high_confidence=high_confidence,
        vendor_names=vendor_names,
        vendor_count=vendor_count,
    )


@app.route("/run-matching", methods=["POST"])
def trigger_matching():
    run_matching()
    return redirect(url_for("ap"))


@app.route("/ap")
def ap():
    invoices = models.Invoice.query.all()
    purchase_orders = models.Purchase_Order.query.all()
    return render_template(
        "ap.html", invoices=invoices, purchase_orders=purchase_orders
    )


@app.route("/model-trainer")
def model_trainer():
    invoices = models.Invoice.query.all()
    invoice_count = len(invoices)
    completed_count = sum(1 for i in invoices if i.status == "complete")
    match_rate = (completed_count / invoice_count * 100) if invoice_count else 0
    scored = [i for i in invoices if i.confidence_score is not None]
    low_confidence = sum(1 for i in scored if i.confidence_score < 50)
    med_confidence = sum(1 for i in scored if 50 <= i.confidence_score < 80)
    high_confidence = sum(1 for i in scored if i.confidence_score >= 80)
    unscored = invoice_count - len(scored)
    avg_confidence = (
        int(sum(i.confidence_score for i in scored) / len(scored)) if scored else 0
    )
    return render_template(
        "model-trainer.html",
        invoice_count=invoice_count,
        match_rate=match_rate,
        low_confidence=low_confidence,
        med_confidence=med_confidence,
        high_confidence=high_confidence,
        unscored=unscored,
        avg_confidence=avg_confidence,
    )


@app.route("/invoice-pdf/<int:invoice_id>")
def get_invoice_pdf(invoice_id):
    directory = os.path.join(app.root_path, "data")
    filename = f"sample_{invoice_id}.pdf"
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return "", 404

    return send_from_directory(directory, filename)


def _is_text_based_pdf(extracted_pdf: dict) -> bool:
    """Return True when pdfplumber found usable text on at least one page."""
    pages = extracted_pdf.get("pages", []) if isinstance(extracted_pdf, dict) else []
    for page in pages:
        text = page.get("text", "") if isinstance(page, dict) else ""
        if text and text.strip():
            return True

    return False


@app.route("/upload-invoice", methods=["GET", "POST"])
def upload_invoice():
    if request.method == "GET":
        flash("Use the upload button on AP page to submit invoices.", "info")
        return redirect(url_for("ap"))

    files = request.files.getlist("invoice_pdf")
    if not files or all(f.filename == "" for f in files):
        return redirect(url_for("ap"))

    upload_dir = os.path.join(app.root_path, "data", "uploads")
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
                    dest = os.path.join(app.root_path, "data", f"sample_{invoice_id}.pdf")
                    shutil.copy(pdf_path, dest)
        except Exception as e:
            app.logger.error(f"Invoice extraction failed for {filename}: {e}")
            flash(f"Could not process '{filename}': {e}", "error")

    return redirect(url_for("ap"))


@app.route("/system-stats")
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


if __name__ == "__main__":
    app.run(debug=True)


# from flask import (
#     Flask,
#     render_template,
#     redirect,
#     url_for,
#     send_from_directory,
#     request,
#     flash,
# )
# from datetime import date, datetime
# import os
# import shutil
# from extensions import db

# app = Flask(__name__)

# basedir = os.path.abspath(os.path.dirname(__file__))
# db_path = os.path.join(basedir, "app.db")

# app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.secret_key = "invoiceai-dev-key"  # Necessary for flash messages (show errors)

# db.init_app(app)


# def format_datetime(value, fmt="%m/%d/%Y"):
#     if value is None:
#         return ""

#     if isinstance(value, datetime):
#         return value.strftime(fmt)

#     if isinstance(value, date):
#         return datetime.combine(value, datetime.min.time()).strftime(fmt)

#     if isinstance(value, str):
#         for parse_fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
#             try:
#                 return datetime.strptime(value, parse_fmt).strftime(fmt)
#             except ValueError:
#                 continue

#     return str(value)


# app.jinja_env.filters["format_datetime"] = format_datetime

# import models
# from po_matching.run_matching import run_matching
# from pdf_parsing.parser import parse_invoice_pdf
# from werkzeug.utils import secure_filename


# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/dashboard")
# def dashboard():
#     invoices = models.Invoice.query.all()
#     purchase_orders = models.Purchase_Order.query.all()
#     pending_count = sum(1 for i in invoices if i.status != "complete")
#     completed_count = sum(1 for i in invoices if i.status == "complete")
#     total_value = sum(i.amount for i in invoices if i.amount)
#     avg_value = total_value / len(invoices) if invoices else 0
#     low_confidence = sum(
#         1
#         for i in invoices
#         if i.confidence_score is not None and i.confidence_score < 50
#     )
#     med_confidence = sum(
#         1
#         for i in invoices
#         if i.confidence_score is not None and 50 <= i.confidence_score < 80
#     )
#     high_confidence = sum(
#         1
#         for i in invoices
#         if i.confidence_score is not None and i.confidence_score >= 80
#     )
#     vendor_names = sorted(set(i.vendor_name for i in invoices if i.vendor_name))
#     vendor_count = len(vendor_names)
#     return render_template(
#         "dashboard.html",
#         invoices=invoices,
#         purchase_orders=purchase_orders,
#         pending_count=pending_count,
#         completed_count=completed_count,
#         total_value=total_value,
#         avg_value=avg_value,
#         low_confidence=low_confidence,
#         med_confidence=med_confidence,
#         high_confidence=high_confidence,
#         vendor_names=vendor_names,
#         vendor_count=vendor_count,
#     )


# @app.route("/run-matching", methods=["POST"])
# def trigger_matching():
#     run_matching()
#     return redirect(url_for("ap"))


# @app.route("/ap")
# def ap():
#     invoices = models.Invoice.query.all()
#     purchase_orders = models.Purchase_Order.query.all()
#     return render_template(
#         "ap.html", invoices=invoices, purchase_orders=purchase_orders
#     )


# @app.route("/model-trainer")
# def model_trainer():
#     invoices = models.Invoice.query.all()
#     invoice_count = len(invoices)
#     completed_count = sum(1 for i in invoices if i.status == "complete")
#     match_rate = (completed_count / invoice_count * 100) if invoice_count else 0
#     scored = [i for i in invoices if i.confidence_score is not None]
#     low_confidence = sum(1 for i in scored if i.confidence_score < 50)
#     med_confidence = sum(1 for i in scored if 50 <= i.confidence_score < 80)
#     high_confidence = sum(1 for i in scored if i.confidence_score >= 80)
#     unscored = invoice_count - len(scored)
#     avg_confidence = (
#         int(sum(i.confidence_score for i in scored) / len(scored)) if scored else 0
#     )
#     return render_template(
#         "model-trainer.html",
#         invoice_count=invoice_count,
#         match_rate=match_rate,
#         low_confidence=low_confidence,
#         med_confidence=med_confidence,
#         high_confidence=high_confidence,
#         unscored=unscored,
#         avg_confidence=avg_confidence,
#     )


# @app.route("/invoice-pdf/<int:invoice_id>")
# def get_invoice_pdf(invoice_id):
#     directory = os.path.join(app.root_path, "data")
#     filename = f"sample_{invoice_id}.pdf"
#     filepath = os.path.join(directory, filename)

#     if not os.path.exists(filepath):
#         return "", 404

#     return send_from_directory(directory, filename)


# @app.route("/upload-invoice", methods=["GET", "POST"])
# def upload_invoice():
#     if request.method == "GET":
#         flash("Use the upload button on AP page to submit invoices.", "info")
#         return redirect(url_for("ap"))

#     files = request.files.getlist("invoice_pdf")
#     if not files or all(f.filename == "" for f in files):
#         return redirect(url_for("ap"))

#     upload_dir = os.path.join(app.root_path, "data", "uploads")
#     os.makedirs(upload_dir, exist_ok=True)

#     for file in files:
#         if not file or file.filename == "":
#             continue

#         if not file.filename.lower().endswith(".pdf"):
#             continue

#         filename = secure_filename(file.filename)
#         pdf_path = os.path.join(upload_dir, filename)
#         file.save(pdf_path)

#         try:
#             invoice_string = parse_invoice_pdf(pdf_path)

#             ## TODO: AI invoice extraction function call.

#         except Exception as e:
#             app.logger.error(f"Invoice extraction failed for {filename}: {e}")
#             flash(f"Could not process '{filename}': {e}", "error")

#     return redirect(url_for("ap"))


# if __name__ == "__main__":
#     app.run(debug=True)