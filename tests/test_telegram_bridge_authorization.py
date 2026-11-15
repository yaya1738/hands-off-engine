"""Telegram inbound commands must be bound to the configured owner identity."""
import importlib
import json
import logging
from unittest.mock import Mock, patch

with patch.object(logging, "basicConfig"):
    bridge_module = importlib.import_module("scripts.telegram_bridge")


def make_bridge(chat_ids=(12345,), user_ids=()):
    bridge = bridge_module.TelegramBridge.__new__(bridge_module.TelegramBridge)
    bridge.config = {
        "token": "test-token",
        "chat_ids": list(chat_ids),
        "user_ids": list(user_ids),
    }
    bridge.available = True
    bridge.state = {"last_update_id": 0, "messages_received": 0}
    return bridge


def test_configured_private_owner_chat_is_authorized():
    bridge = make_bridge()
    assert bridge.is_authorized_message({"chat_id": 12345, "user_id": 12345})


def test_unlisted_chat_is_rejected_even_if_sender_id_matches():
    bridge = make_bridge()
    assert not bridge.is_authorized_message({"chat_id": 99999, "user_id": 99999})


def test_group_chat_requires_explicit_authorized_user_id():
    bridge = make_bridge(chat_ids=(-100777,))
    msg = {"chat_id": -100777, "user_id": 12345}
    assert not bridge.is_authorized_message(msg)

    bridge = make_bridge(chat_ids=(-100777,), user_ids=(12345,))
    assert bridge.is_authorized_message(msg)


def test_missing_sender_identity_fails_closed():
    bridge = make_bridge()
    assert not bridge.is_authorized_message({"chat_id": 12345, "user_id": None})


def test_poll_filters_unauthorized_messages_and_records_rejection():
    bridge = make_bridge()
    updates = {
        "ok": True,
        "result": [
            {"update_id": 1, "message": {
                "chat": {"id": 99999}, "from": {"id": 99999, "username": "stranger"},
                "text": "/trade buy ETH-USD 100", "date": 1,
            }},
            {"update_id": 2, "message": {
                "chat": {"id": 12345}, "from": {"id": 12345, "username": "owner"},
                "text": "/status", "date": 2,
            }},
        ],
    }
    with patch.object(bridge, "_api_call", return_value=updates), \
         patch.object(bridge_module, "save_state") as save:
        messages = bridge.poll_updates(timeout=0)

    assert [m["text"] for m in messages] == ["/status"]
    assert bridge.state["last_update_id"] == 2
    assert bridge.state["messages_received"] == 1
    assert bridge.state["messages_rejected"] == 1
    save.assert_called_once()


def test_dispatch_rechecks_identity_before_treating_sender_as_operator():
    bridge = make_bridge()
    msg = {
        "update_id": 9, "chat_id": 99999, "user_id": 99999,
        "username": "stranger", "text": "/trade buy ETH-USD 100",
    }
    with patch("scripts.comm_hub.CommHub") as comm_hub, \
         patch.object(bridge, "send") as send, \
         patch.object(bridge_module, "save_state"):
        bridge.process_inbound([msg])

    comm_hub.return_value.receive.assert_not_called()
    send.assert_not_called()
    assert bridge.state["messages_rejected"] == 1


def test_authorized_owner_message_reaches_comm_hub_as_operator():
    bridge = make_bridge()
    msg = {
        "update_id": 10, "chat_id": 12345, "user_id": 12345,
        "username": "owner", "text": "/status",
    }
    with patch("scripts.comm_hub.CommHub") as comm_hub, \
         patch.object(bridge, "send"), \
         patch.object(bridge_module, "save_state"):
        comm_hub.return_value.receive.return_value = {"response": "ok"}
        bridge.process_inbound([msg])

    comm_hub.return_value.receive.assert_called_once_with(
        "operator", "status_query", {"query": "full"}, channel="telegram"
    )


def test_group_chat_config_does_not_authorize_any_member_by_default():
    bridge = make_bridge(chat_ids=(-100777,), user_ids=())
    assert not bridge.is_authorized_message({"chat_id": -100777, "user_id": 111})
    assert not bridge.is_authorized_message({"chat_id": -100777, "user_id": 222})


def test_authorized_group_user_does_not_authorize_another_group_member():
    bridge = make_bridge(chat_ids=(-100777,), user_ids=(111,))
    assert bridge.is_authorized_message({"chat_id": -100777, "user_id": 111})
    assert not bridge.is_authorized_message({"chat_id": -100777, "user_id": 222})


def test_config_loader_reads_explicit_group_user_allowlist(tmp_path):
    config_file = tmp_path / "telegram-bridge.json"
    config_file.write_text(json.dumps({
        "botToken": "test-token",
        "chatIds": [-100777],
        "userIds": [111],
    }))
    with patch.object(bridge_module, "TOKEN_FILE", config_file):
        config = bridge_module.load_config()
    assert config == {
        "token": "test-token",
        "chat_ids": [-100777],
        "user_ids": [111],
    }
