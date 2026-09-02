import importlib


MODULE = "scripts.capital_recovery_monitor"


def test_legacy_capital_recovery_surface_is_fail_closed():
    monitor = importlib.import_module(MODULE)

    assert monitor.get_balance() == 0.0
    assert monitor.check_recovery()["trading_enabled"] is False
    assert monitor.check_recovery()["authority_required"] is True
    assert monitor.trigger_singularity_if_ready(50.0) == ["[FACTORY-AUTHORITY] authority_required"]
    assert monitor.save_state({}) is False
    assert monitor.send_telegram("should not send") is False


def test_legacy_monitor_has_no_direct_execution_or_embedded_credentials():
    source = importlib.import_module(MODULE).__loader__.get_source(MODULE)
    assert source is not None
    assert "subprocess" not in source
    assert "requests.post" not in source
    assert "TELEGRAM_BOT_TOKEN" not in source
    assert "AAGkAam" not in source
