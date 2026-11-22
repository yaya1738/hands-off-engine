"""Legacy hourly finance watcher must distinguish unknown from zero."""

import importlib.util
import json
from pathlib import Path

import pytest


WATCHER_PATH = Path("termux-hands-off/agent/finance_watcher.py")
BOT_PATH = Path("termux-hands-off/agent/finance_bot.py")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_watcher(tmp_path):
    watcher = load_module(WATCHER_PATH, "legacy_finance_watcher_test")
    watcher.PM_CANDIDATES = [str(tmp_path / "polymarket.json")]
    watcher.FA_PATH = str(tmp_path / "fiat_accounts.json")
    watcher.CH_PATH = str(tmp_path / "crypto_holdings.json")
    return watcher


def test_missing_sources_produce_unknown_not_zero(tmp_path):
    watcher = make_watcher(tmp_path)

    snapshot = watcher.calc_snapshot()

    assert snapshot["net_usd"] is None
    assert snapshot["estimated_net_usd"] is None
    assert snapshot["status"] == "partial_unknown"
    assert "UNKNOWN" in watcher.build_summary(snapshot, watcher.diff(None, snapshot))


def test_missing_polymarket_fields_are_not_promoted_to_zero(tmp_path):
    watcher = make_watcher(tmp_path)
    (tmp_path / "polymarket.json").write_text(json.dumps({"cash_usd": 0.0}))
    (tmp_path / "fiat_accounts.json").write_text(json.dumps({"bank": 100.0}))
    (tmp_path / "crypto_holdings.json").write_text(json.dumps({"bitcoin": 1.0}))
    watcher.get_coingecko_prices = lambda ids: {"bitcoin": {"usd": 50.0}}

    snapshot = watcher.calc_snapshot()

    assert snapshot["sources"]["polymarket"] == "unknown"
    assert "polymarket_cash_usd" not in snapshot["components"]
    assert snapshot["net_usd"] is None
    assert snapshot["estimated_net_usd"] is None


def test_failed_market_price_is_unknown_not_zero(tmp_path):
    watcher = make_watcher(tmp_path)
    (tmp_path / "polymarket.json").write_text(json.dumps({"cash_usd": 10.0, "mark_value_usd": 5.0}))
    (tmp_path / "fiat_accounts.json").write_text(json.dumps({"bank": 100.0}))
    (tmp_path / "crypto_holdings.json").write_text(json.dumps({"bitcoin": 2.0}))
    watcher.get_coingecko_prices = lambda ids: {}

    snapshot = watcher.calc_snapshot()

    assert snapshot["sources"]["crypto"] == "partial"
    assert "crypto_total_usd" not in snapshot["components"]
    assert snapshot["net_usd"] is None
    assert snapshot["estimated_net_usd"] is None


def test_complete_manual_inputs_are_only_an_unverified_estimate(tmp_path):
    watcher = make_watcher(tmp_path)
    (tmp_path / "polymarket.json").write_text(json.dumps({"cash_usd": 10.0, "mark_value_usd": 5.0}))
    (tmp_path / "fiat_accounts.json").write_text(json.dumps({"bank": 100.0, "debt": -20.0}))
    (tmp_path / "crypto_holdings.json").write_text(json.dumps({"bitcoin": 2.0}))
    watcher.get_coingecko_prices = lambda ids: {"bitcoin": {"usd": 50.0}}

    snapshot = watcher.calc_snapshot()

    assert snapshot["status"] == "unverified_estimate"
    assert snapshot["net_usd"] is None
    assert snapshot["estimated_net_usd"] == 195.0
    assert "Estimated total (UNVERIFIED)" in watcher.build_summary(snapshot, watcher.diff(None, snapshot))


def test_missing_component_does_not_create_zero_delta(tmp_path):
    watcher = make_watcher(tmp_path)
    previous = {"net_usd": 100.0, "components": {"bank": 60.0, "cash": 40.0}}
    current = {"net_usd": None, "components": {"bank": 65.0}}

    result = watcher.diff(previous, current)

    assert result["net_delta"] is None
    assert result["components"] == {"bank": 5.0}


def test_legacy_finance_bot_does_not_default_missing_polymarket_fields_to_zero(tmp_path, monkeypatch):
    bot = load_module(BOT_PATH, "legacy_finance_bot_test")
    state_dir = tmp_path / "state"
    agent_dir = tmp_path / "agent"
    state_dir.mkdir()
    agent_dir.mkdir()
    (state_dir / "polymarket-compact.json").write_text(json.dumps({"cash_usd": 0.0}))
    monkeypatch.setattr(bot, "STATE", str(state_dir))
    monkeypatch.setattr(bot, "AGENT", str(agent_dir))

    result = bot.cmd_pmlatest()

    assert "cash: UNKNOWN" in result
    assert "mark: UNKNOWN" in result
