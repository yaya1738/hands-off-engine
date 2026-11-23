"""Legacy Telegram polling listener must fail closed and bind group commands to a user."""
import importlib
import logging
from unittest.mock import Mock, patch

with patch.object(logging, "FileHandler", lambda *a, **k: logging.NullHandler()):
    listener_module = importlib.import_module("telegram.telegram_bot_listener")


def make_bot(chat_id=None, user_id=None):
    with patch.object(listener_module, "TelegramCommandBot"):
        bot = listener_module.SimpleTelegramBot(
            "fake-token", allowed_chat_id=chat_id, allowed_user_id=user_id
        )
    bot.send_message = Mock(return_value=True)
    return bot


def test_missing_chat_allowlist_fails_closed():
    bot = make_bot()
    message = {"chat": {"id": 123}, "from": {"id": 123}, "text": "/status"}
    assert not bot.is_authorized_message(message)
    with patch.object(bot.command_bot, "process_command") as process:
        bot.process_update({"message": message})
    process.assert_not_called()
    bot.send_message.assert_not_called()


def test_allowlisted_private_chat_authorizes_its_owner():
    bot = make_bot(chat_id=123)
    message = {"chat": {"id": 123}, "from": {"id": 123}, "text": "/status"}
    assert bot.is_authorized_message(message)


def test_unlisted_private_chat_is_rejected():
    bot = make_bot(chat_id=123)
    message = {"chat": {"id": 999}, "from": {"id": 999}, "text": "/trade buy ETH-USD 100"}
    assert not bot.is_authorized_message(message)


def test_group_requires_explicit_user_id():
    message = {"chat": {"id": -100123}, "from": {"id": 123}, "text": "/approve abc"}
    assert not make_bot(chat_id=-100123).is_authorized_message(message)
    assert make_bot(chat_id=-100123, user_id=123).is_authorized_message(message)


def test_process_update_never_executes_command_from_unauthorized_group_member():
    bot = make_bot(chat_id=-100123, user_id=456)
    message = {"chat": {"id": -100123}, "from": {"id": 123}, "text": "/approve abc"}
    with patch.object(bot.command_bot, "process_command") as process:
        bot.process_update({"message": message})
    process.assert_not_called()
    bot.send_message.assert_not_called()


def test_process_update_dispatches_only_authorized_owner_command():
    bot = make_bot(chat_id=123)
    message = {"chat": {"id": 123}, "from": {"id": 123, "username": "owner"}, "text": "/status"}
    with patch.object(bot.command_bot, "process_command", return_value="ok") as process:
        bot.process_update({"message": message})
    process.assert_called_once_with("/status")
    bot.send_message.assert_called_once_with(123, "ok")


def test_listener_refuses_to_start_without_chat_allowlist():
    bot = make_bot()
    with patch.object(bot, "get_updates") as get_updates:
        try:
            bot.run()
        except RuntimeError as exc:
            assert "TELEGRAM_CHAT_ID is required" in str(exc)
        else:
            raise AssertionError("listener unexpectedly started without allowlist")
    get_updates.assert_not_called()
