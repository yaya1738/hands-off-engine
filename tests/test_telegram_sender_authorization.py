import telegram.telegram_command_bot as command_module
from telegram.telegram_command_bot import TelegramCommandBot


def test_privileged_command_requires_allowlisted_sender(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", {"12345"})
    bot = TelegramCommandBot()

    assert "Unauthorized" in bot.process_command("/approve abc", actor_id=None)
    assert "Unauthorized" in bot.process_command("/approve abc", actor_id=67890)


def test_privileged_command_accepts_allowlisted_sender(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", {"12345"})
    bot = TelegramCommandBot()

    # Authorization succeeds and dispatch reaches the command handler.
    # Missing approval ID is then handled by the normal command validation.
    assert "Usage: /approve" in bot.process_command("/approve", actor_id=12345)


def test_privileged_commands_fail_closed_without_configured_admins(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", set())
    bot = TelegramCommandBot()

    assert "Unauthorized" in bot.process_command("/fixssh", actor_id=12345)


def test_setpat_never_accepts_credentials_over_telegram(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", {"12345"})
    bot = TelegramCommandBot()

    response = bot.process_command("/setpat ghp_exampletoken", actor_id=12345)

    assert "disabled" in response
    assert "never send GitHub credentials" in response


def test_sensitive_read_only_queries_require_allowlisted_sender(monkeypatch):
    monkeypatch.setattr(command_module, "ADMIN_USER_IDS", {"12345"})
    bot = TelegramCommandBot()

    assert "Unauthorized" in bot.process_command("/balance", actor_id=None)
    assert "Unauthorized" in bot.process_command("/positions", actor_id=67890)
