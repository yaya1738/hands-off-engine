"""Regression coverage for legacy execution and bankroll fail-closed boundaries."""

import json
import math
import subprocess
from pathlib import Path

import pytest

from finance import truth
from scripts import auto_setup_cron, run_pipeline


def test_pipeline_blocks_when_verified_wallet_balance_is_unknown(monkeypatch):
    monkeypatch.setattr(
        truth,
        "read_verified_polymarket_balance",
        lambda: {
            "verified": False,
            "balance_usdc": None,
            "reason": "stale verification",
        },
    )

    result = run_pipeline.run_pipeline(bankroll=None, dryrun=True, verbose=False)

    assert result["success"] is False
    assert result["blocked"] is True
    assert result["financial_status"] == "unknown"
    assert result["bankroll"] is None
    assert "stale verification" in result["error"]
    assert result["steps"] == {}


def test_pipeline_uses_only_recent_verified_wallet_amount_by_default(monkeypatch):
    monkeypatch.setattr(
        truth,
        "read_verified_polymarket_balance",
        lambda: {"verified": True, "balance_usdc": 42.75},
    )

    amount, status, source, error = run_pipeline.resolve_bankroll(None)

    assert amount == 42.75
    assert status == "verified"
    assert source == "verified_polymarket_wallet"
    assert error is None


def test_explicit_bankroll_is_labeled_modelled_not_verified():
    amount, status, source, error = run_pipeline.resolve_bankroll(250.0)

    assert amount == 250.0
    assert status == "modelled"
    assert source == "explicit_shadow_input"
    assert error is None


@pytest.mark.parametrize("value", [True, -1.0, 0.0, float("nan"), float("inf"), "250"])
def test_invalid_or_nonpositive_bankroll_is_rejected(value):
    amount, status, source, error = run_pipeline.resolve_bankroll(value)

    assert amount is None
    assert error is not None


def test_legacy_cron_installer_and_remover_do_not_mutate_crontab(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("direct crontab mutation must remain disabled")

    monkeypatch.setattr(auto_setup_cron.subprocess, "run", forbidden)
    monkeypatch.setattr(auto_setup_cron.subprocess, "Popen", forbidden)

    assert auto_setup_cron.install_cron_jobs() is False
    assert auto_setup_cron.remove_cron_jobs() is False
    assert calls == []


@pytest.mark.parametrize("script", ["monitor_and_trade.sh", "run_and_notify.sh"])
def test_legacy_shell_trading_entrypoints_fail_closed(script):
    path = Path("scripts") / script
    result = subprocess.run(
        ["bash", str(path)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode != 0
    assert "BLOCKED" in result.stdout
    assert "0xb" not in path.read_text(encoding="utf-8").lower()


def test_legacy_cron_and_trading_registry_entries_are_disabled():
    registry = json.loads(Path("state/script_registry.json").read_text(encoding="utf-8"))

    assert registry["scripts"]["auto_setup_cron"]["enabled"] is False
    assert registry["scripts"]["monitor_and_trade"]["enabled"] is False


def test_shadow_execution_plan_labels_success_as_simulated():
    source = Path("scripts/run_pipeline.py").read_text(encoding="utf-8")

    assert "'simulated' if dryrun and result.success" in source
    assert "'financial_status': results.get('financial_status')" in source
