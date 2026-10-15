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
            "task_id": "task-123", "correlation_id": "task-123",
            "reason_code": "material_ambiguity",
            "context": "Two safe approaches remain.",
            "question": "Which approach should we choose?",
            "why_it_matters": "The answer changes the implementation plan.",
        })
    assert result["status"] == "sent"
    assert result["channel"] == "email"
    assert result["result"]["status"] == "sent"
    assert "task-123" in sender.call_args.kwargs["body"]



def test_correlated_reply_is_advisory_only(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"):
        sent = hub.send("aharon", "coordination", {
            "subject": "Factory question", "text": "What do you think?",
            "task_id": "task-123", "correlation_id": "task-123",
            "reason_code": "material_ambiguity",
            "context": "Two safe approaches remain.",
            "question": "Which approach should we choose?",
            "why_it_matters": "The answer changes the implementation plan.",
        })
    assert sent["status"] == "sent"
    reply = hub.receive_human_reply(
        "aharon", "aharon@example.test", "task-123", "I recommend option B.",
        "provider-message-1",
    )
    assert reply["routed_to"] == "advisory_input"
    assert reply["requires_review"] is True
    assert reply["authority"] == "none"
    bus = (hub.repo_root / "ai" / "coordination" / "messages.jsonl").read_text()
    assert "human_reply_advisory" in bus
    assert "I recommend option B." in bus
    import json
    history = json.loads((hub.state_dir / "human_contact_history.json").read_text())
    assert history[-1]["status"] == "answered"


def test_reply_rejects_sender_mismatch():
    hub = _hub()
    reply = hub.receive_human_reply(
        "aharon", "attacker@example.test", "task-123", "approve", "provider-message-2"
    )
    assert reply["routed_to"] == "rejected"


def test_reply_rejects_unknown_correlation():
    hub = _hub()
    reply = hub.receive_human_reply(
        "aharon", "aharon@example.test", "unknown-task", "hello", "provider-message-3"
    )
    assert reply["routed_to"] == "rejected"


def test_duplicate_reply_is_not_ingested(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"):
        hub.send("aharon", "coordination", {
            "text": "Question", "task_id": "task-dup", "correlation_id": "task-dup",
            "reason_code": "human_context_gap", "context": "A user preference is unknown.",
            "question": "Which preference applies?",
            "why_it_matters": "It changes the next decision.",
        })
    first = hub.receive_human_reply(
        "aharon", "aharon@example.test", "task-dup", "answer", "provider-message-dup"
    )
    second = hub.receive_human_reply(
        "aharon", "aharon@example.test", "task-dup", "answer", "provider-message-dup"
    )
    assert first["routed_to"] == "advisory_input"
    assert second["routed_to"] == "duplicate"


def test_corrupt_reply_dedup_state_fails_closed(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"):
        sent = hub.send("aharon", "coordination", {
            "text": "Need a decision.", "task_id": "task-corrupt-state",
            "correlation_id": "task-corrupt-state",
            "reason_code": "human_context_gap",
            "context": "A required preference is unknown.",
            "question": "Which preference applies?",
            "why_it_matters": "It changes the next decision.",
        })
    assert sent["status"] == "sent"
    (hub.state_dir / "processed_email_replies.json").write_text("{corrupt")
    reply = hub.receive_human_reply(
        "aharon", "aharon@example.test", "task-corrupt-state",
        "some reply", "provider-message-corrupt-state",
    )
    assert reply == {
        "routed_to": "rejected",
        "error": "Reply deduplication state unavailable",
    }
    bus = hub.messages_file.read_text()
    assert "provider-message-corrupt-state" not in bus


def test_non_owner_cannot_approve_or_reject():
    hub = _hub()
    hub.parties["aharon"]["approval_authority"] = False
    result = hub.receive("aharon", "approve", {"command_id": "fake-command"})
    assert result["routed_to"] == "rejected"



def test_human_email_is_blocked_without_task_aware_context(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    with patch("messaging.email_smtp.send_email") as sender:
        result = hub.send("aharon", "coordination", {
            "subject": "Routine status", "text": "Everything is running.",
            "correlation_id": "routine-status-1",
        })
    assert result["status"] == "blocked"
    assert result["result"]["reason"].startswith("missing_context:")
    sender.assert_not_called()


def test_smtp_accepted_but_contact_history_failure_is_reported(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    payload = {
        "text": "Need a decision.", "task_id": "task-history-fail",
        "correlation_id": "task-history-fail",
        "reason_code": "human_context_gap",
        "context": "A required preference is unknown.",
        "question": "Which preference applies?",
        "why_it_matters": "It changes the next decision.",
    }
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"), \
         patch("messaging.human_participant_policy.ContactHistory.record", side_effect=OSError("disk unavailable")):
        result = hub.send("aharon", "coordination", payload)
    assert result["status"] == "sent_audit_incomplete"
    assert result["result"]["transport_accepted"] is True
    assert result["result"]["contact_history_recorded"] is False
    assert result["result"]["correlation_recorded"] is True


def test_smtp_accepted_but_correlation_failure_is_reported(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    hub._record_message_correlation = lambda *_args: (_ for _ in ()).throw(OSError("disk unavailable"))
    payload = {
        "text": "Need a decision.", "task_id": "task-correlation-fail",
        "correlation_id": "task-correlation-fail",
        "reason_code": "human_context_gap",
        "context": "A required preference is unknown.",
        "question": "Which preference applies?",
        "why_it_matters": "It changes the next decision.",
    }
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp"):
        result = hub.send("aharon", "coordination", payload)
    assert result["status"] == "sent_audit_incomplete"
    assert result["result"]["transport_accepted"] is True
    assert result["result"]["correlation_recorded"] is False
    assert result["result"]["audit_error"] == "OSError"


def test_human_email_cooldown_is_enforced_at_send_boundary(monkeypatch):
    hub = _hub()
    monkeypatch.setenv("EMAIL_ALLOWED_RECIPIENTS", "aharon@example.test")
    payload = {
        "text": "Need a decision.", "task_id": "task-rate-1",
        "correlation_id": "task-rate-question-1",
        "reason_code": "material_ambiguity",
        "context": "Two safe paths remain.",
        "question": "Which path should we take?",
        "why_it_matters": "The answer changes the implementation.",
    }
    with patch("messaging.email_smtp.send_email", return_value="accepted_by_smtp") as sender:
        first = hub.send("aharon", "coordination", payload)
        second = hub.send("aharon", "coordination", payload)
    assert first["status"] == "sent"
    assert second["status"] == "blocked"
    assert second["result"]["reason"] in {"duplicate_open_question", "participant_cooldown"}
    assert sender.call_count == 1
