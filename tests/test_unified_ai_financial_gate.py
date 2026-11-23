import json
import subprocess
import sys
from types import SimpleNamespace

import ai.unified_ai as unified_ai


def test_missing_system_state_has_unknown_balance_and_trading_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_ai, "REPO_ROOT", tmp_path)

    state = unified_ai.get_system_state()

    assert state["balance"] is None
    assert state["balance_status"] == "unknown"
    assert state["trading_enabled"] is False
    assert state["micro_trading"] is False


def test_corrupt_system_state_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_ai, "REPO_ROOT", tmp_path)
    state_file = tmp_path / "state" / "unified_system_state.json"
    state_file.parent.mkdir()
    state_file.write_text("{broken", encoding="utf-8")

    state = unified_ai.get_system_state()

    assert state["balance"] is None
    assert state["trading_enabled"] is False
    assert state["state_error"] == "JSONDecodeError"


def test_trading_requires_explicit_state_authorization(monkeypatch):
    monkeypatch.setattr(
        unified_ai, "get_system_state",
        lambda: {"trading_enabled": False, "balance": 1000},
    )
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")

    allowed, reason = unified_ai.check_trading_allowed(5)

    assert allowed is False
    assert "trading_enabled=true" in reason


def test_trading_requires_explicit_environment_authorization(monkeypatch):
    monkeypatch.setattr(
        unified_ai, "get_system_state",
        lambda: {"trading_enabled": True, "balance": 1000},
    )
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)

    allowed, reason = unified_ai.check_trading_allowed(5)

    assert allowed is False
    assert "LIVE_TRADING_ENABLED=1" in reason


def test_unknown_wallet_balance_blocks_trading(monkeypatch):
    monkeypatch.setattr(
        unified_ai, "get_system_state",
        lambda: {"trading_enabled": True},
    )
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")
    fake_module = SimpleNamespace(
        TradingSafeguards=lambda: SimpleNamespace(
            check_wallet_balance=lambda amount: (False, "No funder address configured")
        )
    )
    monkeypatch.setitem(sys.modules, "executor.trading_safeguards", fake_module)

    allowed, reason = unified_ai.check_trading_allowed(5)

    assert allowed is False
    assert "No funder address" in reason


def test_verified_wallet_balance_is_required_for_trading(monkeypatch):
    monkeypatch.setattr(
        unified_ai, "get_system_state",
        lambda: {"trading_enabled": True},
    )
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")
    fake_module = SimpleNamespace(
        TradingSafeguards=lambda: SimpleNamespace(
            check_wallet_balance=lambda amount: (True, "OK - balance: $100.00")
        )
    )
    monkeypatch.setitem(sys.modules, "executor.trading_safeguards", fake_module)

    allowed, reason = unified_ai.check_trading_allowed(5)

    assert allowed is True
    assert "balance: $100.00" in reason


def test_non_positive_or_non_finite_trade_amount_is_rejected(monkeypatch):
    monkeypatch.setattr(
        unified_ai, "get_system_state",
        lambda: {"trading_enabled": True},
    )
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")

    assert unified_ai.check_trading_allowed(0)[0] is False
    assert unified_ai.check_trading_allowed(float("nan"))[0] is False
    assert unified_ai.check_trading_allowed(float("inf"))[0] is False


def test_system_check_never_substitutes_a_fake_bankroll(tmp_path, monkeypatch):
    monkeypatch.setattr(unified_ai, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="", returncode=0),
    )
    fake_module = SimpleNamespace(
        TradingSafeguards=lambda: SimpleNamespace(
            check_wallet_balance=lambda amount: (False, "No funder address configured")
        )
    )
    monkeypatch.setitem(sys.modules, "executor.trading_safeguards", fake_module)

    result = unified_ai.run_system_check()

    assert result["checks"]["balance"]["value"] is None
    assert result["checks"]["balance"]["status"] == "unknown"
    saved = json.loads((tmp_path / "state" / "unified_system_state.json").read_text())
    assert saved["balance"] is None
