import json
from pathlib import Path

from scripts.admission_publisher import publish_admission_decision


def _root(tmp_path: Path) -> Path:
    (tmp_path / "ai" / "coordination").mkdir(parents=True)
    return tmp_path


def test_publisher_uses_canonical_commhub_and_explicit_correlation(tmp_path, monkeypatch):
    root = _root(tmp_path)
    seen = {}

    class FakeHub:
        def __init__(self, repo_root=None):
            seen["repo_root"] = Path(repo_root)

        def receive(self, sender, msg_type, payload, channel=None):
            seen.update({
                "sender": sender,
                "msg_type": msg_type,
                "payload": payload,
                "channel": channel,
            })
            return {"routed_to": "logged", "acknowledged": True}

    monkeypatch.setattr("scripts.admission_publisher.CommHub", FakeHub)

    result = publish_admission_decision(
        {
            "msg_id": "req-1",
            "admitted": True,
            "reason": "ok",
            "decided_at": "2026-09-15T00:00:00Z",
            "context": {"task_id": "task-1"},
            "secret": "must-not-leak",
        },
        repo_root=root,
    )

    assert result == {"status": "published", "msg_id": "req-1"}
    assert seen["sender"] == "factory"
    assert seen["msg_type"] == "task_admission"
    assert seen["channel"] == "messages_jsonl"
    decision = seen["payload"]["decision"]
    assert decision == {
        "msg_id": "req-1",
        "reply_to": "req-1",
        "task_id": "task-1",
        "admitted": True,
        "reason": "ok",
        "decided_at": "2026-09-15T00:00:00Z",
    }
    assert "secret" not in seen["payload"]


def test_duplicate_canonical_admission_is_not_republished(tmp_path, monkeypatch):
    root = _root(tmp_path)
    messages = root / "ai" / "coordination" / "messages.jsonl"
    messages.write_text(json.dumps({
        "type": "inbound_from_agent",
        "payload": {
            "event_type": "task_admission",
            "decision": {"msg_id": "req-1"},
        },
    }) + "\n")

    class ShouldNotCallHub:
        def __init__(self, *args, **kwargs):
            raise AssertionError("duplicate admission must not reach CommHub")

    monkeypatch.setattr("scripts.admission_publisher.CommHub", ShouldNotCallHub)

    assert publish_admission_decision({"msg_id": "req-1"}, repo_root=root) == {
        "status": "already_published",
        "msg_id": "req-1",
    }


def test_invalid_decision_fails_closed(tmp_path):
    assert publish_admission_decision({}, repo_root=_root(tmp_path)) == {
        "status": "skipped",
        "reason": "invalid_decision",
    }
