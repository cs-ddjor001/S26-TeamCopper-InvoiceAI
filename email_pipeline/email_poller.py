import os
import shutil
import threading

from email_pipeline.mailhog_client import process_inbox
from app.extensions import db
from app.models import Invoice
from app.extraction.ai_extractor import extract_invoices_json
from app.extraction.vision_extractor import VisionExtractor
from app.extraction.pdfplumber_extractor import extract_invoice_pdf
from werkzeug.utils import secure_filename


def _is_text_based_pdf(extracted_pdf: dict) -> bool:
    pages = extracted_pdf.get("pages", []) if isinstance(extracted_pdf, dict) else []
    for page in pages:
        text = page.get("text", "") if isinstance(page, dict) else ""
        if text and text.strip():
            return True
    return False


def start_email_poller(app, interval=30):
    def poll():
        while True:
            try:
                with app.app_context():
                    project_root = app.config["PROJECT_ROOT"]
                    upload_dir = os.path.join(project_root, "data", "uploads")
                    os.makedirs(upload_dir, exist_ok=True)

                    for filename, vendor_name, pdf_bytes in process_inbox():
                        safe_name = secure_filename(filename) or "email_invoice.pdf"
                        pdf_path = os.path.join(upload_dir, safe_name)

                        with open(pdf_path, "wb") as f:
                            f.write(pdf_bytes)

                        try:
                            pdf_json = extract_invoice_pdf(pdf_path)

                            if _is_text_based_pdf(pdf_json):
                                results = extract_invoices_json(pdf_json, source_name=safe_name)
                            else:
                                results = [VisionExtractor().extract(pdf_path)]

                            for result in results:

                                invoice_id = result.get("_invoice_id")

                                if invoice_id:
                                    dest = os.path.join(
                                        project_root,
                                        "data",
                                        f"sample_{invoice_id}.pdf"
                                    )

                                    shutil.copy(pdf_path, dest)
                                    invoice = Invoice.query.get(invoice_id)

                                    if invoice:

                                        invoice.vendor_name = vendor_name

                                        # default owner for emailed invoices
                                        invoice.uploaded_by = "tom.ap"

                                        db.session.commit()   

                        except Exception as e:
                            app.logger.error(f"Email poller failed for {safe_name}: {e}")

            except Exception as e:
                app.logger.error(f"Email poller error: {e}")

            threading.Event().wait(interval)

    thread = threading.Thread(target=poll, daemon=True)
    thread.start()