"""Offline tests for authenticated inbound email parsing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from messaging.email_inbox import ingest_raw_reply, poll_inbox
from tests.test_comm_hub_email import _hub


def _raw_email(sender="aharon@example.test", auth="dkim=pass header.d=example.test"):
    return (
        f"From: Aharon <{sender}>\\r\\n"
        "To: factory@example.test\\r\\n"
        "Subject: Re: Factory question\\r\\n"
        f"Authentication-Results: mx.example.test; {auth}\\r\\n"
        "Content-Type: text/plain; charset=utf-8\\r\\n"
        "\\r\\n"
        "I recommend option B.\\r\\n\\r\\n"
        "Reference: task-inbox-1\\r\\n"
    ).encode()


def test_inbound_reply_requires_authentication():
    result = ingest_raw_reply(_hub(), _raw_email(auth="dkim=fail header.d=example.test"), "mail-1")
    assert result["routed_to"] == "rejected"


def test_inbound_reply_requires_reference():
    raw = _raw_email().replace(b"Reference: task-inbox-1\\r\\n", b"No reference here\\r\\n")
    result = ingest_raw_reply(_hub(), raw, "mail-2")
    assert result["routed_to"] == "rejected"


def test_inbound_reply_matches_registered_participant_and_correlation(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    from unittest.mock import patch
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"):
        hub.send("aharon", "coordination", {"text": "Question", "correlation_id": "task-inbox-1"})
    result = ingest_raw_reply(hub, _raw_email(), "mail-3")
    assert result["routed_to"] == "advisory_input"
    assert result["authority"] == "none"


def test_inbox_polling_disabled_without_credentials(monkeypatch):
    for key in ("EMAIL_IMAP_HOST", "EMAIL_IMAP_USERNAME", "EMAIL_IMAP_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    result = poll_inbox(_hub())
    assert result["status"] == "disabled"
