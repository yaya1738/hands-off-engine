from telegram import autonomy_notifier


def test_notify_returns_false_when_messaging_bridge_is_unavailable(monkeypatch):
    class BrokenBridge:
        def __init__(self):
            raise RuntimeError("bridge unavailable")

    monkeypatch.setattr("autonomous.messaging_bridge.MessagingBridge", BrokenBridge)
    assert autonomy_notifier.notify_task_result({"metadata": {"chat_id": "1"}}, {}) is False


def test_notify_routes_summary_through_messaging_bridge(monkeypatch):
    calls = []

    class Bridge:
        def notify(self, message, priority, channel):
            calls.append((message, priority, channel))
            return True

    monkeypatch.setattr("autonomous.messaging_bridge.MessagingBridge", Bridge)
    ok = autonomy_notifier.notify_task_result(
        {"title": "External task", "metadata": {"chat_id": "42"}},
        {"execution": {"success": True, "steps_completed": ["done"]}},
    )

    assert ok is True
    assert calls[0][1:] == ("normal", "all")
    assert "External task" in calls[0][0]
    assert "completed" in calls[0][0]
    assert "done" in calls[0][0]


def test_notify_is_best_effort_when_bridge_returns_false(monkeypatch):
    class Bridge:
        def notify(self, message, priority, channel):
            return False

    monkeypatch.setattr("autonomous.messaging_bridge.MessagingBridge", Bridge)
    assert autonomy_notifier.notify_task_result({"title": "External task"}, {}) is False
