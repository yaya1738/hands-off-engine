from telegram import autonomy_notifier


def test_notify_returns_false_without_external_destination(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert autonomy_notifier.notify_task_result({"metadata": {"chat_id": "1"}}, {}) is False


def test_notify_returns_false_without_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert autonomy_notifier.notify_task_result({"metadata": {"chat_id": "1"}}, {}) is False


def test_notify_posts_summary(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")

    class Response:
        def raise_for_status(self):
            return None

    calls = []

    class Requests:
        @staticmethod
        def post(url, json, timeout):
            calls.append((url, json, timeout))
            return Response()

    monkeypatch.setitem(__import__("sys").modules, "requests", Requests)
    ok = autonomy_notifier.notify_task_result(
        {"title": "External task", "metadata": {"chat_id": "42"}},
        {"execution": {"success": True, "steps_completed": ["done"]}},
    )

    assert ok is True
    assert calls[0][1]["chat_id"] == "42"
    assert "completed" in calls[0][1]["text"]
