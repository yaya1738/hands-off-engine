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



def test_empty_polymarket_response_preserves_previous_mark(tmp_path, monkeypatch, capsys):
    private_root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_root))
    agent_dir = str(AGENTS.resolve())
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "private_polymarket_positions_test",
        AGENTS / "polymarket_positions.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "load_wallet", lambda: "0x" + "1" * 40)
    monkeypatch.setattr(module, "fetch_positions", lambda wallet: [])

    module.main()

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unknown"
    assert result["mark_sum"] is None
    assert not module.EXT.exists()



def test_manual_external_account_metadata_is_never_summed_into_net_worth(tmp_path, monkeypatch):
    private_root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_root))
    agent_dir = str(AGENTS.resolve())
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "private_finance_watcher_manual_test",
        AGENTS / "finance_watcher.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXTERNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    module.EXTERNAL_FILE.write_text(json.dumps({
        "bank_balance": 1000,
        "credit_limit": 5000,
        "credit_score": 700,
        "rent_monthly": 1500,
        "life_notes": {"note": "metadata"},
    }), encoding="utf-8")

    snapshot = module.portfolio_snapshot({})

    assert snapshot["external_status"] == "manual_unverified"
    assert snapshot["external_manual_inputs_present"] is True
    assert snapshot["usd_total_raw"] is None
    assert snapshot["usd_total"] is None
    assert snapshot["status"] == "partial_unknown"



def test_finance_vault_importer_writes_only_to_private_secrets_directory(tmp_path):
    env = os.environ.copy()
    env["HANDS_OFF_PRIVATE_DIR"] = str(tmp_path / "private")
    env.pop("OKX_API_KEY", None)
    env.pop("OKX_API_SECRET", None)
    env.pop("OKX_API_PASSPHRASE", None)
    env.pop("KRAKEN_API_KEY", None)
    env.pop("KRAKEN_API_SECRET", None)
    result = subprocess.run(
        [sys.executable, str(AGENTS / "finance_vault_from_any.py")],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    vault = tmp_path / "private" / "secrets" / "vault.json"
    data = json.loads(vault.read_text(encoding="utf-8"))
    assert all(value == "" for value in data.values())
    assert vault.stat().st_mode & 0o777 == 0o600
    assert "private" in result.stdout.lower()


def test_legacy_finance_watcher_reads_only_migrated_private_runtime_state(tmp_path, monkeypatch):
    private_root = tmp_path / "private"
    monkeypatch.setenv("HANDS_OFF_PRIVATE_DIR", str(private_root))
    agent_dir = str(Path("termux-hands-off/agent").resolve())
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "private_legacy_finance_watcher_test",
        Path("termux-hands-off/agent/finance_watcher.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.STATE == str(private_root / "legacy_runtime" / "state")
    assert module.AGENT == str(private_root / "legacy_runtime" / "agent")
    assert module.LOGDIR == str(private_root / "logs")
