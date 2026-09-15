from pathlib import Path

import pytest

from scripts.interaction_bridge import correlate_event, send_operator_message


def test_correlate_event_preserves_message_and_task_identity():
    event = {
        "id": "msg-1",
        "type": "task_result",
        "timestamp": "2026-09-15T00:00:00+00:00",
        "payload": {"context": {"task_id": "task-1"}, "reply_to": "msg-0"},
    }

    assert correlate_event(event) == {
        "msg_id": "msg-1",
        "task_id": "task-1",
        "reply_to": "msg-0",
        "type": "task_result",
        "timestamp": "2026-09-15T00:00:00+00:00",
    }


def test_correlate_event_accepts_flat_task_id():
    result = correlate_event({"msg_id": "m", "task_id": "t", "type": "task_assignment"})
    assert result["msg_id"] == "m"
    assert result["task_id"] == "t"


def test_operator_message_is_rejected_before_transport(tmp_path: Path):
    with pytest.raises(ValueError, match="1-4000"):
        send_operator_message(tmp_path, "   ")


def test_operator_message_uses_supplied_checkout_root(tmp_path: Path, monkeypatch):
    class FakeHub:
        def __init__(self, repo_root):
            assert repo_root == tmp_path

        def receive(self, sender, msg_type, payload, channel):
            assert sender == "operator"
            assert msg_type == "inbound_from_operator"
            assert payload["message"] == "inspect status"
            assert channel == "interaction_bridge"
            return {"routed_to": "logged", "acknowledged": True}

    monkeypatch.setattr("scripts.comm_hub.CommHub", FakeHub)
    result = send_operator_message(tmp_path, "inspect status", reply_to="msg-previous")
    assert result["status"] == "sent"
    assert result["transport"] == "ai/coordination/messages.jsonl"
    assert result["governance"] == "CommHub.receive"
    assert result["result"]["acknowledged"] is True
