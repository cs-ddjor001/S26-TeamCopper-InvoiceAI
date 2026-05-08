import smtplib
from email.message import EmailMessage
from pathlib import Path

msg = EmailMessage()
msg["From"] = "vendor@example.com"
msg["To"] = "invoices@ads.com"
msg["Subject"] = "Invoice #12345"
msg.set_content("Please find the attached invoice.")

repo_root = Path(__file__).parent

pdf_path = repo_root.parent / "data" / "ADS_invoice_data" / "11-10977887.pdf"
#file existance verification
if not pdf_path.exists():
    print(f"Error: PDF file not found at {pdf_path}")
    
msg.add_attachment(
    pdf_path.read_bytes(),
    maintype="application",
    subtype="pdf",
    filename=pdf_path.name,
)

with smtplib.SMTP("localhost", 1025) as smtp:
    smtp.send_message(msg)

print("Sent with attachment.")