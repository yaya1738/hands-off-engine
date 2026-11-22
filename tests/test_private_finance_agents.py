"""Legacy finance agents must not turn missing private inputs into zero."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


AGENTS = Path("termux-hands-off/agents")


def test_finance_watcher_reports_unknown_when_private_accounts_are_missing(tmp_path, monkeypatch):
    private_root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_root))
    agent_dir = str(AGENTS.resolve())
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "private_finance_watcher_test",
        AGENTS / "finance_watcher.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    snapshot = module.portfolio_snapshot({})

    assert snapshot["status"] == "partial_unknown"
    assert snapshot["external_status"] == "unknown"
    assert snapshot["usd_total_raw"] is None
    assert snapshot["usd_total"] is None


def test_rotate_today_blocks_when_private_cash_is_unknown(tmp_path):
    env = os.environ.copy()
    env["HANDS_OFF_PRIVATE_DIR"] = str(tmp_path / "private")
    result = subprocess.run(
        [sys.executable, str(AGENTS / "rotate_today.py")],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["status"] == "blocked_unknown_cash"
    assert output["cash_available"] is None
    assert output["actions"] == []


def test_credit_guardrail_displays_unknown_cash_when_private_file_is_missing(tmp_path):
    env = os.environ.copy()
    env["HANDS_OFF_PRIVATE_DIR"] = str(tmp_path / "private")
    result = subprocess.run(
        [sys.executable, str(AGENTS / "credit_guardrail.py")],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert "Cash UNKNOWN" in result.stdout
    log = tmp_path / "private" / "legacy_runtime" / "logs" / "guardrail_actions.log"
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert record["cash_liquid"] is None


def test_balance_entry_forms_keep_blank_unknown_values_as_null(tmp_path):
    env = os.environ.copy()
    env["HANDS_OFF_PRIVATE_DIR"] = str(tmp_path / "private")
    blank_inputs = "\n\n\n\n"
    result = subprocess.run(
        [sys.executable, str(AGENTS / "balances_fill.py")],
        input=blank_inputs,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    path = tmp_path / "private" / "legacy_runtime" / "agents" / "external_accounts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert all(data[key] is None for key in ("paypal", "monzo", "robinhood_cash", "polymarket_cash"))
