import telegram.telegram_command_bot as command_module
import telegram.telegram_bot_listener as listener_module


def test_all_operational_commands_require_allowlisted_sender(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", {"77123"})
    bot = command_module.TelegramCommandBot.__new__(command_module.TelegramCommandBot)
    bot.commands = {
        "/approve": lambda args: "approved",
        "/status": lambda args: "status",
        "/help": lambda args: "help",
    }

    assert "Denied" in bot.process_command("/approve abc")
    assert "Denied" in bot.process_command("/status")
    assert "Denied" in bot.process_command("/approve abc", actor_id="other")
    assert bot.process_command("/approve abc", actor_id=77123) == "approved"
    assert bot.process_command("/status", actor_id="77123") == "status"
    assert bot.process_command("/help") == "help"


def test_missing_admin_allowlist_fails_closed(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", set())
    bot = command_module.TelegramCommandBot.__new__(command_module.TelegramCommandBot)
    bot.commands = {"/approve": lambda args: "approved"}
    assert "Denied" in bot.process_command("/approve abc", actor_id="77123")


def test_setpat_is_disabled_and_never_accepts_chat_credentials():
    bot = command_module.TelegramCommandBot.__new__(command_module.TelegramCommandBot)
    response = bot.cmd_setpat(["ghp_never-store-this"])
    assert "Disabled" in response
    assert "secure out-of-band" in response


def test_listener_requires_private_chat_and_allowlisted_sender(monkeypatch):
    monkeypatch.setattr(listener_module, "ADMIN_USER_IDS", {"77123"})
    monkeypatch.setattr(listener_module, "ALLOWED_CHAT_ID", "77123")
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
    bot.process_update({"message": {
        "chat": {"id": 77123, "type": "private"},
        "from": {"id": 77123, "username": "allowed"},
        "text": "/approve abc",
    }})
    assert calls == [("/approve abc", 77123)]


def test_listener_fails_closed_when_admin_allowlist_missing(monkeypatch):
    monkeypatch.setattr(listener_module, "ADMIN_USER_IDS", set())
    bot = listener_module.SimpleTelegramBot.__new__(listener_module.SimpleTelegramBot)
    bot.command_bot = type("CommandBot", (), {"process_command": lambda *args, **kwargs: "should not run"})()
    bot.send_message = lambda *args, **kwargs: True
    bot.process_update({"message": {
        "chat": {"id": 77123, "type": "private"},
        "from": {"id": 77123},
        "text": "/status",
    }})


