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
