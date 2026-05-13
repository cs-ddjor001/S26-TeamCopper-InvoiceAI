import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_test_invoice_email(smtp_host: str = "localhost", smtp_port: int = 1025) -> None:
    """Send a sample invoice PDF to MailHog for end-to-end pipeline testing."""
    pdf_path = Path(__file__).parent.parent / "data" / "sample_5.pdf"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Test PDF not found at {pdf_path}")

    msg = EmailMessage()
    msg["From"] = "vendor@example.com"
    msg["To"] = "invoices@ads.com"
    msg["Subject"] = "Invoice #12345"
    msg.set_content("Please find the attached invoice.")
    msg.add_attachment(
        pdf_path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=pdf_path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.send_message(msg)


if __name__ == "__main__":
    send_test_invoice_email()
    print("Sent with attachment.")
