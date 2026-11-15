import json
from datetime import datetime, timezone

from scripts.authority_classification import classify_and_publish
from scripts.command_approval import command_fingerprint


class FakeHub:
    def __init__(self, **kwargs):
        self.received = None

    def receive(self, sender_id, msg_type, payload, channel):
        self.received = (sender_id, msg_type, payload, channel)
        return {"routed_to": "messages_jsonl"}


def _approved_command(tmp_path):
    state = tmp_path / "state"
    state.mkdir(parents=True, exist_ok=True)
    command = {
        "id": "m-live", "source": "test", "action": "execute", "target": "factory",
        "payload": {"action": "factory_execute", "objective": "continue"},
        "mode": "LIVE", "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": 5, "sync": False, "timeout_seconds": 300,
        "queued_at": datetime.now(timezone.utc).isoformat(), "approval_status": "approved",
    }
    fingerprint = command_fingerprint(command)
    command["approval_fingerprint"] = fingerprint
    (state / "approval_queue.json").write_text(json.dumps({
        "pending": [],
        "approved": [{
            "id": command["id"], "approved_at": datetime.now(timezone.utc).isoformat(),
            "fingerprint": fingerprint,
        }],
        "rejected": [],
    }))
    return command


def test_classifies_dryrun_and_preserves_correlation(monkeypatch):
    hub = FakeHub()
    monkeypatch.setattr("scripts.authority_classification.CommHub", lambda **kwargs: hub)
    result = classify_and_publish({
        "id": "m-1", "mode": "DRYRUN", "approval_status": "pending",
        "objective": "continue",
        "correlation": {"msg_id": "m-1", "task_id": "t-1", "reply_to": "m-0"},
    })
    assert result["status"] == "published"
    decision = hub.received[2]["decision"]
    assert decision["command_id"] == "m-1"
    assert decision["msg_id"] == "m-1"
    assert decision["task_id"] == "t-1"
    assert decision["reply_to"] == "m-0"
    assert decision["decision"] == "dryrun_only"
    assert decision["execution_enabled"] is False
    assert decision["approval_required"] is False
    datetime.fromisoformat(decision["decided_at"])


def test_live_flag_without_durable_record_is_not_reported_as_approved(monkeypatch, tmp_path):
    hub = FakeHub()
    monkeypatch.setattr("scripts.authority_classification.CommHub", lambda **kwargs: hub)
    result = classify_and_publish({
        "id": "m-2", "mode": "LIVE", "approval_status": "approved",
        "correlation": {"msg_id": "m-2", "task_id": "t-2"},
    }, repo_root=tmp_path, execution_gate=True)
    assert result["status"] == "published"
    decision = hub.received[2]["decision"]
    assert decision["decision"] == "approval_required"
    assert decision["execution_enabled"] is False


def test_live_durable_approval_is_classified_consistently(monkeypatch, tmp_path):
    hub = FakeHub()
    monkeypatch.setattr("scripts.authority_classification.CommHub", lambda **kwargs: hub)
    command = _approved_command(tmp_path)
    result = classify_and_publish(command, repo_root=tmp_path, execution_gate=True)
    assert result["status"] == "published"
    decision = hub.received[2]["decision"]
    assert decision["decision"] == "approved"
    assert decision["execution_enabled"] is False


def test_invalid_command_fails_closed_without_bus_write(monkeypatch):
    called = False
    def fail_hub(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("invalid input must not reach the bus")
    monkeypatch.setattr("scripts.authority_classification.CommHub", fail_hub)
    assert classify_and_publish(None) == {"status": "rejected", "reason": "invalid_command"}
    assert called is False
