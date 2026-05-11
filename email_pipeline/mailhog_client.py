"""
Email ingestion client for the AI² invoice processing pipeline.

Pulls emails from a local MailHog dev server, extracts PDF attachments,
and hands raw bytes to downstream processing stages.
"""

import email
import email.policy
from urllib.parse import quote

import requests


def list_message_ids(base_url: str = "http://localhost:8025") -> list[str]:
    """Return all message IDs currently held in the MailHog inbox.

    MailHog's GET /api/v1/messages response is a flat JSON array.  Each
    element is a message object shaped like:

        {
            "ID":      "<id-string>@mailhog.example",
            "From":    { "Mailbox": "...", "Domain": "...", ... },
            "To":      [ { ... } ],
            "Content": { "Headers": { ... }, "Body": "..." },
            "MIME":    { "Parts": [ ... ] },
            "Raw":     { "From": "...", "To": [...], "Data": "<rfc5322 string>", "Helo": "..." },
            "Created": "<timestamp>"
        }

    This function is the entry point of the ingestion loop: it tells the
    pipeline which messages exist before any heavy I/O (fetch + parse)
    is attempted.
    """
    response = requests.get(f"{base_url}/api/v1/messages")
    response.raise_for_status()
    return [msg["ID"] for msg in response.json()]


def fetch_raw_email(message_id: str, base_url: str = "http://localhost:8025") -> bytes:
    """Fetch a single message's raw RFC 5322 bytes from MailHog.

    MailHog exposes the raw email under the "Raw.Data" field of
    GET /api/v1/messages/{id}.  Note: there is no /download endpoint in
    standard MailHog — Raw.Data is the canonical source of the wire-format
    email.

    The message ID contains '=' and '@' which must be percent-encoded when
    used as a URL path segment; quote(safe="") encodes all non-unreserved
    characters to prevent the request from being misrouted.

    Returning bytes (not str) keeps the contract clean for email.message_from_bytes()
    downstream, which expects the raw octets of the message.
    """
    encoded_id = quote(message_id, safe="")
    response = requests.get(f"{base_url}/api/v1/messages/{encoded_id}")
    response.raise_for_status()
    return response.json()["Raw"]["Data"].encode("utf-8")


def extract_pdf_attachments(raw_email: bytes) -> list[tuple[str, bytes]]:
    """Parse a raw RFC 5322 email and return all PDF attachments as (filename, bytes) pairs.

    Uses policy=email.policy.default so the message object exposes the modern
    API — iter_attachments(), get_content_type(), get_filename() — rather than
    the legacy walk()-based interface from email.policy.compat32.

    Both content-type and filename extension are checked because senders
    sometimes mislabel application/octet-stream with a .pdf filename, or
    attach PDFs under a generic MIME type.

    get_payload(decode=True) is used instead of get_content() because for
    non-text parts (application/*) get_content() raises an error; get_payload
    with decode=True always returns the decoded bytes regardless of the
    Content-Transfer-Encoding (base64, quoted-printable, etc.).
    """
    msg = email.message_from_bytes(raw_email, policy=email.policy.default)
    results: list[tuple[str, bytes]] = []
    for part in msg.iter_attachments():
        filename = part.get_filename() or ""
        is_pdf_type = part.get_content_type() == "application/pdf"
        is_pdf_name = filename.lower().endswith(".pdf")
        if is_pdf_type or is_pdf_name:
            results.append((filename, part.get_payload(decode=True)))
    return results


def process_inbox() -> list[tuple[str, bytes]]:
    """Walk every message in the MailHog inbox and return all PDF attachments found.

    Returns a flat list of (filename, pdf_bytes) tuples collected across all
    messages in the inbox — one entry per PDF attachment.  The caller is
    responsible for routing these into the invoice processing pipeline.
    """
    message_ids = list_message_ids()
    all_pdfs: list[tuple[str, bytes]] = []

    for message_id in message_ids:
        raw = fetch_raw_email(message_id)
        all_pdfs.extend(extract_pdf_attachments(raw))

    return all_pdfs


if __name__ == "__main__":
    for filename, pdf_bytes in process_inbox():
        print(f"{filename!r} — {len(pdf_bytes):,} bytes")
