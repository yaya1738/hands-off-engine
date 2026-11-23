from scripts import capital_recovery_monitor as monitor


def test_unknown_balance_does_not_become_zero_or_update_recovery_state(monkeypatch):
    original = {
        "last_balance": 250.0,
        "last_balance_verified": True,
        "trading_enabled": True,
        "alerts_sent": [],
        "recovery_events": [],
    }
    monkeypatch.setattr(monitor, "get_balance", lambda: None)
    monkeypatch.setattr(monitor, "load_state", lambda: dict(original))
    monkeypatch.setattr(monitor, "log_event", lambda event: None)
    monkeypatch.setattr(
        monitor,
        "save_state",
        lambda state: (_ for _ in ()).throw(AssertionError("unknown balance must not be persisted")),
    )

    result = monitor.check_recovery()

    assert result["balance"] is None
    assert result["balance_status"] == "unknown"
    assert result["trading_enabled"] is False


def test_verified_capital_threshold_never_enables_live_trading(monkeypatch):
    saved = {}
    state = {
        "last_balance": 49.0,
        "last_balance_verified": True,
        "trading_enabled": False,
        "alerts_sent": [],
        "recovery_events": [],
    }
    monkeypatch.setattr(monitor, "get_balance", lambda: 250.0)
    monkeypatch.setattr(monitor, "load_state", lambda: dict(state))
    monkeypatch.setattr(monitor, "save_state", lambda value: saved.update(value))
    monkeypatch.setattr(monitor, "log_event", lambda event: None)
    monkeypatch.setattr(monitor, "send_telegram", lambda *args, **kwargs: True)

    result = monitor.check_recovery()

    assert result["balance_status"] == "verified"
    assert result["trading_enabled"] is False
    assert saved["trading_enabled"] is False
    assert "capital_review" in saved["alerts_sent"]


def test_legacy_singularity_trigger_is_blocked(monkeypatch):
    monkeypatch.setattr(monitor, "log_event", lambda event: None)

    assert monitor.trigger_singularity_if_ready(500.0) is False
