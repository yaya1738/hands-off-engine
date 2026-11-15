import telegram.telegram_command_bot as command_module
import telegram.telegram_bot_listener as listener_module


def test_approval_commands_require_authenticated_allowlisted_user(monkeypatch):
    monkeypatch.setattr(command_module, "TELEGRAM_USER_ID", "77123")
    bot = command_module.TelegramCommandBot.__new__(command_module.TelegramCommandBot)
    bot.commands = {"/approve": lambda args: "approved"}

    assert "Denied" in bot.process_command("/approve abc")
    assert "Denied" in bot.process_command("/approve abc", actor_id="other")
    assert bot.process_command("/approve abc", actor_id=77123) == "approved"


def test_approval_commands_fail_closed_when_user_allowlist_missing(monkeypatch):
    monkeypatch.setattr(command_module, "TELEGRAM_USER_ID", None)
    bot = command_module.TelegramCommandBot.__new__(command_module.TelegramCommandBot)
    bot.commands = {"/approve": lambda args: "approved"}

    assert "Denied" in bot.process_command("/approve abc", actor_id="77123")


def test_listener_requires_private_chat_and_matching_chat_and_user(monkeypatch):
    monkeypatch.setattr(listener_module, "ALLOWED_CHAT_ID", "77123")
    monkeypatch.setattr(listener_module, "ALLOWED_USER_ID", "77123")
    bot = listener_module.SimpleTelegramBot.__new__(listener_module.SimpleTelegramBot)
    calls = []
    bot.command_bot = type("CommandBot", (), {
        "process_command": lambda self, text, actor_id=None: calls.append((text, actor_id)) or "ok"
    })()
    bot.send_message = lambda chat_id, response: True

    bot.process_update({"message": {
        "chat": {"id": 77123, "type": "group"},
        "from": {"id": 77123, "username": "allowed"},
        "text": "/approve abc",
    }})
    bot.process_update({"message": {
        "chat": {"id": 77123, "type": "private"},
        "from": {"id": 99999, "username": "allowed"},
        "text": "/approve abc",
    }})
    assert calls == []

    bot.process_update({"message": {
        "chat": {"id": 77123, "type": "private"},
        "from": {"id": 77123, "username": "allowed"},
        "text": "/approve abc",
    }})
    assert calls == [("/approve abc", 77123)]
