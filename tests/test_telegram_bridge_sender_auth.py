import scripts.telegram_bridge as bridge_module


def test_telegram_bridge_rejects_unlisted_users_and_non_private_chats(monkeypatch):
    bridge = bridge_module.TelegramBridge.__new__(bridge_module.TelegramBridge)
    bridge.config = {"user_ids": ["77123"]}
    sent = []
    bridge.send = lambda text, chat_id=None: sent.append((text, chat_id))
    calls = []

    class Hub:
        def receive(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {"routed_to": "logged"}

    monkeypatch.setattr(bridge_module, "load_config", lambda: bridge.config)
    monkeypatch.setattr("scripts.comm_hub.CommHub", lambda: Hub())

    bridge.process_inbound([
        {"text": "/approve cmd-1", "chat_id": 77123, "chat_type": "group", "user_id": 77123},
        {"text": "/approve cmd-1", "chat_id": 77123, "chat_type": "private", "user_id": 99999},
    ])

    assert calls == []
    assert len(sent) == 2


def test_telegram_bridge_passes_verified_actor_identity(monkeypatch):
    bridge = bridge_module.TelegramBridge.__new__(bridge_module.TelegramBridge)
    bridge.config = {"user_ids": ["77123"]}
    bridge.send = lambda *args, **kwargs: None
    calls = []

    class Hub:
        def receive(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {"routed_to": "approval_workflow", "result": {"status": "denied"}}

    monkeypatch.setattr("scripts.comm_hub.CommHub", lambda: Hub())

    bridge.process_inbound([
        {"text": "/approve cmd-1", "chat_id": 77123, "chat_type": "private", "user_id": 77123}
    ])

    assert len(calls) == 1
    assert calls[0][0][0:2] == ("operator", "approve")
    assert calls[0][1]["authenticated"] is True
    assert calls[0][1]["authenticated_actor_id"] == "77123"
