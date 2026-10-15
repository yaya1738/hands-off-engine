"""Optional IMAP reply ingestion for the human-participant email loop.

Disabled unless private IMAP configuration is complete. Messages are accepted
only when the receiving mail server's Authentication-Results header shows SPF
or DKIM pass for the sender's domain, and CommHub validates participant and
correlation policy again. Replies are advisory only.
"""
import imaplib
import os
import re
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr


_REFERENCE = re.compile(r"(?im)^\\s*Reference\\s*:\\s*([A-Za-z0-9._:-]{1,200})\\s*$")


def _decoded(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _authenticated_sender_domain(message, sender_email):
    sender_domain = sender_email.rsplit("@", 1)[-1].casefold()
    headers = message.get_all("Authentication-Results", [])
    for header in headers:
        value = str(header).casefold()
        for match in re.finditer(r"dkim=pass\\s+header\\.d=([^;\\s]+)", value):
            domain = match.group(1).strip(".")
            if sender_domain == domain or sender_domain.endswith("." + domain):
                return True
        for match in re.finditer(r"spf=pass\\s+smtp\\.mailfrom=([^;\\s]+)", value):
            mailbox = match.group(1).strip("<>")
            domain = mailbox.rsplit("@", 1)[-1].strip(".")
            if domain and (sender_domain == domain or sender_domain.endswith("." + domain)):
                return True
    return False


def _plain_text(message):
    parts = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                try:
                    parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    elif message.get_content_type() == "text/plain":
        try:
            parts.append(message.get_content())
        except Exception:
            payload = message.get_payload(decode=True) or b""
            parts.append(payload.decode(message.get_content_charset() or "utf-8", errors="replace"))
    return "\\n".join(parts)[:12000]


def ingest_raw_reply(hub, raw_message, provider_message_id):
    """Parse and pass a raw email to CommHub, failing closed on weak identity."""
    message = message_from_bytes(raw_message)
    _, sender = parseaddr(_decoded(message.get("From", "")))
    sender = sender.strip().casefold()
    if not sender or not _authenticated_sender_domain(message, sender):
        return {"routed_to": "rejected", "error": "Sender authentication failed"}
    body = _plain_text(message)
    reference_match = _REFERENCE.search(body)
    if not reference_match:
        return {"routed_to": "rejected", "error": "Missing reference"}
    candidates = [
        party_id for party_id, party in hub.parties.items()
        if party.get("role") == "human_participant"
        and party.get("email_consent") is True
        and "email" in party.get("channels", [])
        and str(party.get("email", "")).strip().casefold() == sender
    ]
    if len(candidates) != 1:
        return {"routed_to": "rejected", "error": "Sender is not a unique enabled participant"}
    return hub.receive_human_reply(
        candidates[0], sender, reference_match.group(1), body,
        provider_message_id, channel="email",
    )


def poll_inbox(hub, *, imap_factory=None, limit=25):
    """Poll unseen messages over IMAPS; no-op until private settings are complete."""
    host = os.getenv("EMAIL_IMAP_HOST", "").strip()
    username = os.getenv("EMAIL_IMAP_USERNAME", "").strip()
    password = os.getenv("EMAIL_IMAP_PASSWORD", "")
    folder = os.getenv("EMAIL_IMAP_FOLDER", "INBOX").strip() or "INBOX"
    if not all((host, username, password)):
        return {"status": "disabled", "reason": "IMAP configuration incomplete", "processed": 0}
    factory = imap_factory or imaplib.IMAP4_SSL
    processed = 0
    rejected = 0
    try:
        with factory(host) as mailbox:
            mailbox.login(username, password)
            status, _ = mailbox.select(folder)
            if status != "OK":
                return {"status": "error", "reason": "Could not select inbox", "processed": 0}
            status, data = mailbox.search(None, "UNSEEN")
            if status != "OK":
                return {"status": "error", "reason": "Inbox search failed", "processed": 0}
            ids = (data[0].split() if data and data[0] else [])[-max(1, min(int(limit), 100)):]
            for message_id in ids:
                status, fetched = mailbox.fetch(message_id, "(BODY.PEEK[])")
                if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                    continue
                raw = fetched[0][1]
                result = ingest_raw_reply(hub, raw, message_id.decode("ascii", errors="replace"))
                processed += 1
                if result.get("routed_to") not in ("advisory_input", "duplicate"):
                    rejected += 1
                # Mark each handled message seen so it is not repeatedly ingested.
                mailbox.store(message_id, "+FLAGS", "\\Seen")
            return {"status": "ok", "processed": processed, "rejected": rejected}
    except Exception as exc:
        return {"status": "error", "reason": type(exc).__name__, "processed": processed, "rejected": rejected}
