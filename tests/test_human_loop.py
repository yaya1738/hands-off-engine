from pathlib import Path

from telegram.communication_protocol import ConversationStore
from telegram.human_loop import HumanLoop


def test_human_loop_persists_and_queues_request(tmp_path: Path, monkeypatch):
    captured = {}

    class FakeQueue:
        def __init__(self, root):
            captured["root"] = root

        def add_task(self, **kwargs):
            captured["task"] = kwargs
            return "12345678-task"

    import scripts.autonomous_task_queue as module
    monkeypatch.setattr(module, "AutonomousTaskQueue", FakeQueue)

    response = HumanLoop(tmp_path).receive("Continue autonomously.", chat_id="42", username="yair")

    assert "12345678" in response
    assert captured["task"]["source"] == "telegram_user"
    assert captured["task"]["metadata"]["chat_id"] == "42"
    assert captured["task"]["metadata"]["communication_message_id"]
    messages = ConversationStore(tmp_path).read()
    assert len(messages) == 2
    assert messages[0].direction == "inbound"
    assert messages[1].direction == "outbound"
    assert messages[1].correlation_id == messages[0].message_id
