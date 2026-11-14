import scripts.telegram_bridge as bridge_module
from scripts.telegram_bridge import TelegramBridge


def test_telegram_bridge_rejects_unlisted_sender_before_commhub(monkeypatch):
    from scripts.comm_hub import CommHub

    received = []
    monkeypatch.setattr(bridge_module, "ADMIN_USER_IDS", {"111"})
    monkeypatch.setattr(CommHub, "__init__", lambda self: None)
    monkeypatch.setattr(
        CommHub,
        "receive",
        lambda self, *args, **kwargs: received.append((args, kwargs)) or {"routed_to": "approval_workflow"},
    )

    bridge = TelegramBridge.__new__(TelegramBridge)
    bridge.available = False
    bridge.process_inbound([{
        "user_id": 222,
        "chat_id": 999,
        "username": "untrusted",
        "text": "/approve sensitive-command",
    }])

    assert received == []


def test_telegram_bridge_passes_allowlisted_sender_to_operator_workflow(monkeypatch):
    from scripts.comm_hub import CommHub

    received = []
    monkeypatch.setattr(bridge_module, "ADMIN_USER_IDS", {"111"})
    monkeypatch.setattr(CommHub, "__init__", lambda self: None)
    monkeypatch.setattr(
        CommHub,
        "receive",
        lambda self, *args, **kwargs: received.append((args, kwargs)) or {"routed_to": "approval_workflow"},
    )

    bridge = TelegramBridge.__new__(TelegramBridge)
    bridge.available = False
    bridge.process_inbound([{
        "user_id": 111,
        "chat_id": 999,
        "username": "admin",
        "text": "/approve sensitive-command",
    }])

    assert len(received) == 1
    assert received[0][0][0:2] == ("operator", "approve")


def test_telegram_bridge_fails_closed_when_allowlist_missing(monkeypatch):
    from scripts.comm_hub import CommHub

    received = []
    monkeypatch.setattr(bridge_module, "ADMIN_USER_IDS", set())
    monkeypatch.setattr(CommHub, "__init__", lambda self: None)
    monkeypatch.setattr(
        CommHub,
        "receive",
        lambda self, *args, **kwargs: received.append((args, kwargs)) or {},
    )

    bridge = TelegramBridge.__new__(TelegramBridge)
    bridge.available = False
    bridge.process_inbound([{
        "user_id": 111,
        "chat_id": 999,
        "username": "admin",
        "text": "/trade buy ETH-USD 10",
    }])

    assert received == []
