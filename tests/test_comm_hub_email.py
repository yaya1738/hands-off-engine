"""No-network tests for guarded human-participant email delivery."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.comm_hub import CommHub, DEFAULT_PARTIES
from messaging.email_smtp import send_email


def _hub():
    tmp = Path(tempfile.mkdtemp())
    hub = CommHub.__new__(CommHub)
    hub.repo_root = tmp
    hub.state_dir = tmp / "state"
    hub.state_dir.mkdir()
    hub.comm_log = hub.state_dir / "comm_log.jsonl"
    hub.messages_file = tmp / "ai" / "coordination" / "messages.jsonl"
    hub.messages_file.parent.mkdir(parents=True)
    hub.inbound_dir = hub.state_dir / "inbound"
    hub.inbound_dir.mkdir()
    hub.outbound_dir = hub.state_dir / "outbound"
    hub.outbound_dir.mkdir()
    hub.parties = {**DEFAULT_PARTIES, "aharon": {
        "id": "aharon", "name": "Aharon", "role": "human_participant",
        "trust_level": 1, "channels": ["email"], "info_scope": "project_summary",
        "notify_on": ["coordination", "task_assignment", "system_status"],
        "format": "human_readable", "email": "aharon@example.test",
        "email_consent": True,
    }}
    hub.pending_acks = {}
    return hub


def test_email_requires_explicit_consent(monkeypatch):
    hub = _hub()
    hub.parties["aharon"]["email_consent"] = False
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email") as sender:
        result = hub.send("aharon", "coordination", {"text": "hello"})
    assert result["result"]["status"] == "blocked"
    sender.assert_not_called()


def test_email_requires_allowlist(monkeypatch):
    hub = _hub()
    monkeypatch.delenv("EMAIL_ALLOWED_RECIPIENTS", raising=False)
    with patch("messaging.email_smtp.send_email") as sender:
        result = hub.send("aharon", "coordination", {"text": "hello"})
    assert result["result"]["status"] == "blocked"
    sender.assert_not_called()


def test_email_transport_requires_private_config(monkeypatch):
    for key in ("EMAIL_SMTP_HOST", "EMAIL_SMTP_USERNAME", "EMAIL_SMTP_PASSWORD", "EMAIL_FROM"):
        monkeypatch.delenv(key, raising=False)
    with patch("messaging.email_smtp.smtplib.SMTP_SSL") as smtp:
        try:
            send_email("aharon@example.test", "subject", "body")
        except ValueError as exc:
            assert "not fully configured" in str(exc)
        else:
            raise AssertionError("missing config must fail closed")
    smtp.assert_not_called()


def test_email_delivery_uses_mocked_transport(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp") as sender:
        result = hub.send("aharon", "coordination", {
            "subject": "Factory question", "text": "What do you think?",
            "correlation_id": "task-123",
        })
    assert result["status"] == "sent"
    assert result["channel"] == "email"
    assert result["result"]["status"] == "sent"
    assert "task-123" in sender.call_args.kwargs["body"]
