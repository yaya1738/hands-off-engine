import json

from scripts.authority_decision_publisher import publish_authority_decision


def test_invalid_decision_fails_closed(tmp_path):
    assert publish_authority_decision({}, repo_root=tmp_path) == {
        "status": "skipped",
        "reason": "invalid_decision",
    }


def test_publishes_bounded_decision_to_canonical_bus(tmp_path):
    result = publish_authority_decision(
        {
            "msg_id": "m-1",
            "reply_to": "m-0",
            "task_id": "t-1",
            "decision": "approval_required",
            "reason": "live work requires explicit approval",
            "approval_required": True,
            "execution_enabled": False,
            "decided_at": "2026-09-15T00:00:00+00:00",
            "secret": "must-not-escape",
        },
        repo_root=tmp_path,
    )
    assert result == {"status": "published", "msg_id": "m-1"}
    lines = (tmp_path / "ai" / "coordination" / "messages.jsonl").read_text().splitlines()
    event = json.loads(lines[-1])
    decision = event["payload"]["decision"]
    assert event["payload"]["event_type"] == "authority_decision"
    assert decision["msg_id"] == "m-1"
    assert decision["task_id"] == "t-1"
    assert decision["reply_to"] == "m-0"
    assert decision["execution_enabled"] is False
    assert "secret" not in decision


def test_duplicate_decision_is_idempotent(tmp_path):
    decision = {"msg_id": "m-2", "decision": "denied"}
    assert publish_authority_decision(decision, repo_root=tmp_path)["status"] == "published"
    assert publish_authority_decision(decision, repo_root=tmp_path)["status"] == "already_published"
