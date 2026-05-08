import smtplib
from email.message import EmailMessage
from pathlib import Path

msg = EmailMessage()
msg["From"] = "vendor@example.com"
msg["To"] = "invoices@ads.com"
msg["Subject"] = "Invoice #12345"
msg.set_content("Please find the attached invoice.")

pdf_path = Path("test_invoice.pdf")
msg.add_attachment(
    pdf_path.read_bytes(),
    maintype="application",
    subtype="pdf",
    filename=pdf_path.name,
)

with smtplib.SMTP("localhost", 1025) as smtp:
    smtp.send_message(msg)

print("Sent with attachment.")