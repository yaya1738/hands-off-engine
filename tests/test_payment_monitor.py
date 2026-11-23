"""Regression tests for the payment monitor's financial evidence boundary."""

import json
from datetime import datetime, timezone

import pytest

from scripts import payment_monitor as monitor


def test_payment_monitor_uses_repository_relative_private_state_path():
    assert monitor.STATE_FILE == monitor.BASE_DIR / "state" / "payment_monitor.json"
    assert "/root/hands-off-engine" not in str(monitor.STATE_FILE)


def test_wallet_address_is_loaded_from_private_environment(monkeypatch):
    wallet = "0x" + "a" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    assert monitor._load_wallet_configuration() == wallet


def test_missing_or_invalid_wallet_fails_closed(monkeypatch):
    monkeypatch.delenv("POLYMARKET_FUNDER_ADDRESS", raising=False)
    assert monitor._load_wallet_configuration() is None
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", "0x1234")
    assert monitor._load_wallet_configuration() is None


def test_non_polygon_chain_is_unknown_and_does_not_query_tokens(monkeypatch):
    calls = []
    monkeypatch.setattr(monitor, "get_chain_id", lambda: 1)
    monkeypatch.setattr(monitor, "get_erc20_balance", lambda *args: calls.append(args))
    assert monitor.get_verified_balance("0x" + "a" * 40) is None
    assert calls == []


def test_both_usdc_contracts_must_be_verified(monkeypatch):
    calls = []
    monkeypatch.setattr(monitor, "get_chain_id", lambda: monitor.POLYGON_CHAIN_ID)

    def balance(wallet, contract):
        calls.append(contract)
        return 12.5 if contract == monitor.USDC_NATIVE else None

    monkeypatch.setattr(monitor, "get_erc20_balance", balance)
    assert monitor.get_verified_balance("0x" + "a" * 40) is None
    assert calls == [monitor.USDC_NATIVE, monitor.USDC_BRIDGED]


def test_complete_balance_requires_both_tokens_and_sums_them(monkeypatch):
    values = {
        monitor.USDC_NATIVE: 12.5,
        monitor.USDC_BRIDGED: 7.5,
    }
    monkeypatch.setattr(monitor, "get_chain_id", lambda: monitor.POLYGON_CHAIN_ID)
    monkeypatch.setattr(monitor, "get_erc20_balance", lambda wallet, contract: values[contract])
    assert monitor.get_verified_balance("0x" + "a" * 40) == (20.0, 12.5, 7.5)


def test_unknown_observation_does_not_create_or_mutate_state(tmp_path, monkeypatch):
    state_file = tmp_path / "payment_monitor.json"
    monkeypatch.setattr(monitor, "STATE_FILE", state_file)
    monkeypatch.setattr(monitor, "_load_wallet_configuration", lambda: "0x" + "a" * 40)
    monkeypatch.setattr(monitor, "get_verified_balance", lambda wallet: None)

    result = monitor.main()

    assert result == {"status": "unknown", "balance_usdc": None}
    assert not state_file.exists()


def test_first_observation_is_baseline_not_income(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "STATE_FILE", tmp_path / "payment_monitor.json")
    now = datetime.now(timezone.utc)

    state, previous, payment = monitor.record_balance_observation(50.0, now)

    assert previous is None
    assert payment is None
    assert state["last_balance"] == 50.0
    assert state["payments"] == []


def test_verified_increase_is_recorded_once(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "STATE_FILE", tmp_path / "payment_monitor.json")
    now = datetime.now(timezone.utc)
    monitor.record_balance_observation(50.0, now)

    state, previous, payment = monitor.record_balance_observation(65.0, now)

    assert previous == 50.0
    assert payment["amount"] == 15.0
    assert state["payments"] == [payment]


@pytest.mark.parametrize("value", [True, -1.0, float("nan"), float("inf"), "10"])
def test_invalid_observation_cannot_mutate_state(tmp_path, monkeypatch, value):
    state_file = tmp_path / "payment_monitor.json"
    monkeypatch.setattr(monitor, "STATE_FILE", state_file)

    with pytest.raises(ValueError):
        monitor.record_balance_observation(value, datetime.now(timezone.utc))

    assert not state_file.exists()


def test_missing_telegram_credentials_does_not_make_request(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert monitor.send_telegram("test") is False
