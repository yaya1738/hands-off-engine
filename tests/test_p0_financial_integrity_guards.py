"""P0 regression tests for financial-input and legacy execution boundaries."""

import math
from datetime import datetime, timezone, timedelta
import json
import pytest
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

from autonomous import capital_vessel
from autonomous.capital_vessel import (
    CapitalVessel,
    Compartment,
    FlowValve,
    VesselCompartment,
)
from autonomous.script_manager import ScriptManager
from autonomous.power_plant import FuelTank, Generator, PowerPlant
from autonomous.architecture_session import ArchitectureSession, EconomicsArchitect
from autonomous.vessel_filler import VesselFiller
from autonomous.claude_optimizer import ClaudeOptimizer
from autonomous import singularity_trigger
from revenue.master_revenue_engine import MasterRevenueEngine
from scripts.executor import Executor as GovernedExecutor
from scripts import executor as governed_executor_module
from executor import trading_safeguards
from scripts import recalibrate_engine, resume_trading
from hardware.trading_protection import TradingProtectionManager
from autonomous.fuel_system import FuelDetector, FuelSystem, FuelType
from scripts import capital_recovery_monitor
from finance.truth import read_verified_polymarket_balance
from finance import refresh_balances
from audit.ledger import FinancialLedger
from finance import dashboard as finance_dashboard
from autonomous.system_doctor import SystemDoctor
from autonomous.actuators import PolymarketActuator
from autonomous.process_endpoints import ENDPOINT_REGISTRY, ProcessCycler
from executor.trading_safeguards import TradingSafeguards
from executor.ho_executor_plan import Executor


def test_script_manager_execution_and_cron_mutations_fail_closed(monkeypatch):
    manager = ScriptManager()
    manager.registry["scripts"] = {
        "example": {
            "path": "scripts/example.py",
            "type": "python",
            "enabled": True,
        }
    }

    def forbidden(*args, **kwargs):
        raise AssertionError("legacy manager must not execute subprocesses")

    monkeypatch.setattr("autonomous.script_manager.subprocess.run", forbidden)
    monkeypatch.setattr("autonomous.script_manager.subprocess.Popen", forbidden)

    ok, message = manager.run_script("example")
    assert ok is False
    assert "FactoryAuthorityGateway" in message
    assert manager.add_cron_job("example", "*/5 * * * *")[0] is False
    assert manager.remove_cron_job("example")[0] is False


def test_wallet_verification_failure_is_not_permission(tmp_path, monkeypatch):
    safeguards = TradingSafeguards(performance_log=tmp_path / "trades.jsonl")
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", "0x" + "1" * 40)
    monkeypatch.setattr(safeguards, "_get_usdc_balance", lambda *_: None)

    allowed, message = safeguards.check_wallet_balance(0)

    assert allowed is False
    assert "Could not verify" in message


def test_native_usdc_unknown_makes_aggregate_balance_unknown(tmp_path, monkeypatch):
    safeguards = TradingSafeguards(performance_log=tmp_path / "trades.jsonl")
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", "0x" + "1" * 40)
    values = iter([12.0, None])
    monkeypatch.setattr(safeguards, "_get_usdc_balance", lambda *_: next(values))

    allowed, message = safeguards.check_wallet_balance(1)

    assert allowed is False
    assert "native USDC" in message


def test_position_size_rejects_nonpositive_and_nonfinite_values(tmp_path):
    safeguards = TradingSafeguards(performance_log=tmp_path / "trades.jsonl")

    for value in (0, -1, math.nan, math.inf, -math.inf):
        allowed, _ = safeguards.check_position_size(value)
        assert allowed is False


def test_compartment_and_valve_reject_invalid_amounts():
    compartment = VesselCompartment(
        name="test",
        purpose="test",
        capacity=100.0,
        contents=50.0,
    )
    valve = FlowValve(name="test", direction="inlet", max_flow=100.0)

    for value in (0, -1, math.nan, math.inf, -math.inf):
        assert compartment.deposit(value) == 0.0
        assert compartment.withdraw(value) == 0.0
        assert valve.can_flow(value) is False
        assert valve.flow(value) == 0.0

    assert compartment.contents == 50.0
    assert valve.daily_used == 0.0


def test_capital_vessel_transfer_rejects_negative_and_nonfinite_amounts(tmp_path, monkeypatch):
    monkeypatch.setattr(capital_vessel, "VESSEL_STATE", tmp_path / "vessel.json")
    monkeypatch.setattr(capital_vessel, "VESSEL_LOG", tmp_path / "vessel.jsonl")
    vessel = CapitalVessel()
    source = vessel.compartments[Compartment.TRADING]
    destination = vessel.compartments[Compartment.BUFFER]
    source.contents = 100.0
    before = (source.contents, destination.contents)

    for value in (-5, 0, math.nan, math.inf, -math.inf):
        result = vessel.transfer(value, Compartment.TRADING, Compartment.BUFFER)
        assert result["transferred"] == 0.0

    assert (source.contents, destination.contents) == before



def test_legacy_power_plant_trade_path_is_blocked():
    generator = Generator()
    result = generator.generate({"token_id": "example"}, 10.0)

    assert result["success"] is False
    assert result["status"] == "blocked"
    assert result["execution_authorized"] is False
    assert generator.trades_executed == 0
    assert generator.total_consumed == 0.0


def test_power_plant_cycle_never_books_estimated_profit_or_spends_fuel():
    plant = PowerPlant.__new__(PowerPlant)
    plant.state = {"cycles": 0}
    plant.fuel_tank = FuelTank(current_level=100.0)
    plant.turbine = SimpleNamespace(rotate=lambda: [{"token_id": "example"}])
    plant.generator = Generator()

    class NoTransfer:
        def transfer(self, amount):
            raise AssertionError("unrealized profit must never be transferred")

    plant.grid = NoTransfer()
    plant._save_state = lambda: None
    plant._log_generation = lambda event: None

    result = plant.cycle()

    assert result["watts_generated"] == 0.0
    assert result["trades"][0]["status"] == "blocked"
    assert plant.fuel_tank.current_level == 100.0
    assert plant.generator.total_generated == 0.0


def test_unverified_position_resolution_cannot_mutate_accounting():
    plant = PowerPlant.__new__(PowerPlant)
    result = plant.process_resolution("unverified-position", 500.0)

    assert result["status"] == "blocked"
    assert result["accounting_mutated"] is False
    assert result["execution_authorized"] is False



def test_force_flag_cannot_bypass_actuator_safeguards():
    calls = []
    actuator = PolymarketActuator.__new__(PolymarketActuator)
    actuator.trader = SimpleNamespace(
        place_market_order_usd=lambda *args: calls.append(args) or {"orderID": "unexpected"}
    )
    actuator._check_trading_mode = lambda: (True, "ok")
    actuator._check_safeguards = lambda amount: (True, "ok")

    forced = actuator.place_market_order("token", 10.0, "BUY", force=True)
    ordinary = actuator.place_market_order("token", 10.0, "BUY", force=False)

    assert forced.get("blocked_by") == "governed_execution"
    assert ordinary.get("blocked_by") == "governed_execution"
    assert calls == []


def test_process_cycler_cannot_directly_execute_polymarket_trade():
    calls = []
    cycler = ProcessCycler.__new__(ProcessCycler)
    cycler.actuators = SimpleNamespace(
        trade=lambda *args, **kwargs: calls.append((args, kwargs))
    )

    result = cycler._execute_actuator(
        ENDPOINT_REGISTRY["trading_execute"],
        {"token_id": "token", "amount": 10.0, "side": "BUY"},
    )

    assert result["success"] is False
    assert result["execution_authorized"] is False
    assert result["blocked_by"] == "governed_execution"
    assert calls == []



def test_generator_resolution_cannot_book_unverified_profit():
    generator = Generator()
    before = (generator.total_generated, generator.trades_won)

    result = generator.record_resolution(500.0)

    assert result["status"] == "blocked"
    assert result["accounting_mutated"] is False
    assert (generator.total_generated, generator.trades_won) == before


def test_power_plant_never_funds_itself_from_local_financial_cache():
    plant = PowerPlant.__new__(PowerPlant)
    plant.fuel_tank = FuelTank(current_level=241.36, pending_fuel=99.0)

    result = plant._sync_fuel_from_reality()

    assert result["status"] == "unknown"
    assert result["spendable_balance"] is None
    assert plant.fuel_tank.current_level == 0.0
    assert plant.fuel_tank.pending_fuel == 0.0


def test_capital_vessel_refuses_unverified_financial_snapshot():
    vessel = CapitalVessel.__new__(CapitalVessel)
    vessel.compartments = {
        Compartment.OPERATING: SimpleNamespace(contents=8.99),
        Compartment.TRADING: SimpleNamespace(contents=98.05),
    }

    result = vessel.sync_from_reality()

    assert result["status"] == "blocked"
    assert result["accounting_mutated"] is False
    assert vessel.compartments[Compartment.OPERATING].contents == 8.99
    assert vessel.compartments[Compartment.TRADING].contents == 98.05


def test_architecture_context_never_falls_back_to_historical_balances(tmp_path, monkeypatch):
    monkeypatch.setattr("autonomous.architecture_session.STATE_DIR", tmp_path)
    (tmp_path / "financial_state.json").write_text(
        '{"balance": 241.36, "positions_value": 999.0}'
    )
    session = ArchitectureSession.__new__(ArchitectureSession)

    context = session._gather_context()
    analysis = EconomicsArchitect()._analyze("power economics", context)

    assert context["balance"] == "unknown"
    assert context["positions"] == "unknown"
    assert "Current verified balance: unknown" in analysis
    assert "8.99" not in analysis
    assert "98.05" not in analysis


def test_vessel_filler_blocks_stale_balance_and_position_assumptions():
    filler = VesselFiller.__new__(VesselFiller)

    trade = filler._action_micro_trade()
    positions = filler._action_wait_positions()

    assert trade["status"] == "blocked"
    assert trade["execution_authorized"] is False
    assert positions["status"] == "blocked"
    assert positions["automatic_deposit"] is False


def test_optimizer_does_not_treat_cached_balances_as_truth():
    optimizer = ClaudeOptimizer.__new__(ClaudeOptimizer)

    result = optimizer._get_financial_state()

    assert result["balance"] == "unknown"
    assert result["positions"] == "unknown"
    assert result["source"] == "no_verified_financial_truth_adapter"


def test_legacy_cash_planner_has_no_static_bankroll_or_trade_sizing():
    path = Path(__file__).resolve().parents[1] / "scripts" / "activate_cash_generation.py"
    spec = importlib.util.spec_from_file_location("legacy_cash_generation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.generate_execution_plan()

    assert result["status"] == "blocked"
    assert result["bankroll"] is None
    assert result["trades"] == []
    assert result["execution_authorized"] is False



def test_process_cycler_cannot_run_arbitrary_scripts():
    cycler = ProcessCycler.__new__(ProcessCycler)
    result = cycler._execute_script(
        SimpleNamespace(target="scripts/activate_cash_generation.py", args=[]),
        {},
    )

    assert result["success"] is False
    assert result["execution_authorized"] is False
    assert result["blocked_by"] == "governed_execution"


def test_legacy_executor_never_reports_fake_live_orders():
    executor = Executor.__new__(Executor)
    executor.dryrun = False
    action = SimpleNamespace(
        market_id="market",
        market_name="test market",
        confidence=0.95,
        amount=25.0,
        side="YES",
    )

    result = executor.execute_actions([action])[0]

    assert result.success is False
    assert result.executed_amount == 0.0
    assert "no governed live execution adapter" in result.message


def test_legacy_executor_rejects_invalid_position_amounts():
    executor = Executor.__new__(Executor)
    executor.dryrun = True

    for amount in (0, -1, math.nan, math.inf, -math.inf):
        action = SimpleNamespace(
            market_id="market",
            market_name="test market",
            confidence=0.95,
            amount=amount,
            side="YES",
        )
        allowed, message = executor.validate_action(action)
        assert allowed is False
        assert "position" in message.lower()



def test_singularity_threshold_is_observation_only(tmp_path, monkeypatch):
    monkeypatch.setattr(singularity_trigger, "TRIGGER_STATE", tmp_path / "trigger.json")
    monkeypatch.setattr(singularity_trigger, "get_balance", lambda: 55.0)
    notifications = []
    monkeypatch.setattr(
        singularity_trigger,
        "send_telegram",
        lambda *args, **kwargs: notifications.append((args, kwargs)) or True,
    )

    result = singularity_trigger.check_and_trigger()

    assert result["threshold_status"] == "full_threshold_observed"
    assert result["approval_required"] is True
    assert result["execution_authorized"] is False
    assert result["trading_enabled"] is False
    assert "triggered" not in result or result["triggered"] is False
    assert notifications


def test_singularity_unknown_balance_does_not_become_zero_or_trigger(tmp_path, monkeypatch):
    monkeypatch.setattr(singularity_trigger, "TRIGGER_STATE", tmp_path / "trigger.json")
    monkeypatch.setattr(singularity_trigger, "get_balance", lambda: None)

    result = singularity_trigger.check_and_trigger()

    assert result["financial_status"] == "unknown"
    assert result["last_balance"] is None
    assert result["execution_authorized"] is False
    assert result["trading_enabled"] is False


def test_legacy_singularity_execution_functions_are_blocked():
    full = singularity_trigger.execute_singularity()
    mini = singularity_trigger.execute_mini_singularity(100.0)

    assert full[0]["status"] == "blocked"
    assert mini[0]["status"] == "blocked"
    assert full[0]["execution_authorized"] is False
    assert mini[0]["execution_authorized"] is False



def test_revenue_engine_does_not_publish_unverified_profit_forecasts():
    engine = MasterRevenueEngine()
    projection = engine.generate_full_revenue_projection()
    polymarket = engine.get_polymarket_revenue_potential()

    assert projection["projection_status"] == "UNVERIFIED"
    assert projection["total_monthly_potential"] is None
    assert projection["current_burn"] is None
    assert polymarket["current_capital"] is None
    assert polymarket["monthly_expected"] is None
    assert polymarket["execution_authorized"] is False

    actions = engine.get_immediate_actions()
    assert all("LIVE_TRADING_ENABLED" not in action.get("command", "") for action in actions)
    assert all("Execute Polymarket trades" != action["action"] for action in actions)


def test_singularity_trigger_contains_no_embedded_telegram_credentials():
    path = Path(__file__).resolve().parents[1] / "autonomous" / "singularity_trigger.py"
    source = path.read_text()

    assert "8214203655" not in source
    assert "8327766663" not in source
    assert "subprocess.run" not in source
    assert "TELEGRAM_BOT_TOKEN" in source
    assert "TELEGRAM_CHAT_ID" in source



def test_governed_executor_requires_durable_authority_before_live(tmp_path):
    executor = GovernedExecutor.__new__(GovernedExecutor)
    executor.state_dir = tmp_path
    executor.rate_limit_state = {"window_start": __import__("time").time(), "count": 0}
    command = {
        "id": "live-command-without-durable-approval",
        "mode": "LIVE",
        "approval_status": "approved",
        "queued_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "target": "executor",
        "payload": {"action": "trade", "params": {"amount": 10.0}},
    }

    result = executor.execute_command(command, execution_gate=True)

    assert result.status == "rejected"
    assert "Approval missing, mismatched" in result.error


def test_governed_executor_never_reports_stub_backends_as_executed():
    executor = GovernedExecutor.__new__(GovernedExecutor)
    command = {
        "id": "direct-live-backend-call",
        "mode": "LIVE",
        "target": "executor",
        "payload": {"action": "trade", "params": {"amount": 10.0}},
    }

    result = executor._live_execute(command)
    trade = executor._execute_trade({"amount": 10.0})
    control = executor._execute_system_control("resume", {})

    assert result.status == "rejected"
    assert trade["status"] == "blocked"
    assert control["status"] == "blocked"
    assert trade["execution_authorized"] is False
    assert control["accounting_mutated"] is False


def test_governed_executor_rejects_invalid_trade_amounts():
    executor = GovernedExecutor.__new__(GovernedExecutor)

    for amount in (0, -1, math.nan, math.inf, -math.inf, "10"):
        result = executor._validate_action({
            "payload": {"action": "trade", "params": {"amount": amount}}
        })
        assert result["ok"] is False



def test_auto_resume_never_enables_live_trading(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("auto-resume must not read or mutate trading mode")

    monkeypatch.setattr(trading_safeguards, "load_mode", forbidden)
    monkeypatch.setattr(trading_safeguards, "save_mode", forbidden)

    assert trading_safeguards.maybe_auto_resume("good_performance", notify=False) is False


def test_recalibration_never_resumes_live_trading():
    mode = {"live_trading_enabled": False, "auto_paused": True}
    before = dict(mode)

    resumed = recalibrate_engine.maybe_resume_trading(
        {"phase": "baby_mode"},
        {"hit_rate": 0.9, "total_pnl": 1000, "trade_count": 100},
        mode,
    )

    assert resumed is False
    assert mode == before


def test_legacy_resume_command_does_not_change_trading_state():
    assert resume_trading.main() == 2



def test_hardware_auto_recovery_cannot_clear_trading_protection():
    manager = TradingProtectionManager.__new__(TradingProtectionManager)

    assert manager.resume_trading(reason="hardware_recovered") is False



def test_governed_executor_requires_execution_enabled_from_authority(tmp_path, monkeypatch):
    executor = GovernedExecutor.__new__(GovernedExecutor)
    executor.state_dir = tmp_path
    executor.rate_limit_state = {"window_start": __import__("time").time(), "count": 0}
    executor._check_approval_binding = lambda command: True
    executor._check_approval_freshness = lambda command: True
    executor._check_rate_limit = lambda: True
    executor._validate_action = lambda command: {"ok": True, "reason": None}
    monkeypatch.setattr(
        governed_executor_module,
        "authorize",
        lambda *args, **kwargs: SimpleNamespace(
            decision="approved",
            execution_enabled=False,
            reason="authority layer never grants execution",
        ),
    )
    command = {
        "id": "approved-but-not-execution-enabled",
        "mode": "LIVE",
        "approval_status": "approved",
        "target": "executor",
        "payload": {"action": "trade", "params": {"amount": 10.0}},
    }

    result = executor.execute_command(command, execution_gate=True)

    assert result.status == "rejected"
    assert "Governed authority did not grant execution" in result.error



def test_fuel_detector_never_counts_unverified_cached_positions():
    detector = FuelDetector()

    assert detector.scan_positions() == []


def test_fuel_status_excludes_positions_and_marks_cash_unknown():
    system = FuelSystem.__new__(FuelSystem)
    system.state = {
        "detected_deposits": [
            {"fuel_type": FuelType.POSITION.value, "estimated_amount": 900.0},
            {"fuel_type": FuelType.CONSULTING.value, "estimated_amount": 250.0},
        ]
    }

    status = system.get_fuel_status()

    assert status["financial_status"] == "unknown"
    assert status["liquid_fuel"] == 0.0
    assert status["pending_fuel"] == 0.0
    assert status["detected_deposits"] == 1
    assert status["total_detected"] == 250.0


def test_capital_recovery_monitor_unknown_balance_stays_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(capital_recovery_monitor, "STATE_FILE", tmp_path / "recovery.json")
    monkeypatch.setattr(capital_recovery_monitor, "LOG_FILE", tmp_path / "recovery.log")
    monkeypatch.setattr(capital_recovery_monitor, "get_balance", lambda: None)

    result = capital_recovery_monitor.check_recovery()

    assert result["balance"] is None
    assert result["financial_status"] == "unknown"
    assert result["trading_enabled"] is False
    assert result["execution_authorized"] is False
    assert result["events"] == []


def test_capital_recovery_threshold_is_observation_not_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(capital_recovery_monitor, "STATE_FILE", tmp_path / "recovery.json")
    monkeypatch.setattr(capital_recovery_monitor, "LOG_FILE", tmp_path / "recovery.log")
    monkeypatch.setattr(capital_recovery_monitor, "get_balance", lambda: 60.0)
    (tmp_path / "recovery.json").write_text(
        json.dumps({"last_balance": 40.0, "recovery_events": [], "alerts_sent": []})
    )
    notifications = []
    monkeypatch.setattr(
        capital_recovery_monitor,
        "send_telegram",
        lambda *args, **kwargs: notifications.append(args) or True,
    )

    result = capital_recovery_monitor.check_recovery()

    assert result["approval_required"] is True
    assert result["trading_enabled"] is False
    assert result["execution_authorized"] is False
    assert result["events"][0]["position_resolution_verified"] is False
    assert notifications


def test_legacy_capital_recovery_trigger_is_blocked():
    result = capital_recovery_monitor.trigger_singularity_if_ready(1000.0)

    assert result["status"] == "blocked"
    assert result["execution_authorized"] is False


def test_capital_recovery_monitor_has_no_embedded_telegram_credentials_or_subprocess():
    path = Path(__file__).resolve().parents[1] / "scripts" / "capital_recovery_monitor.py"
    source = path.read_text()

    assert "8214203655" not in source
    assert "8327766663" not in source
    assert "subprocess.run" not in source
    assert "TELEGRAM_BOT_TOKEN" in source
    assert "TELEGRAM_CHAT_ID" in source



def test_capital_vessel_cannot_create_or_claim_withdrawn_cash_without_adapters():
    vessel = CapitalVessel.__new__(CapitalVessel)
    before = {
        Compartment.OPERATING: SimpleNamespace(contents=12.0),
        Compartment.TRADING: SimpleNamespace(contents=40.0),
    }
    vessel.compartments = before

    deposit = vessel.deposit(100.0, Compartment.OPERATING)
    withdrawal = vessel.withdraw(20.0, Compartment.OPERATING)

    assert deposit["status"] == "blocked"
    assert deposit["deposited"] == 0.0
    assert withdrawal["status"] == "blocked"
    assert withdrawal["withdrawn"] == 0.0
    assert before[Compartment.OPERATING].contents == 12.0
    assert before[Compartment.TRADING].contents == 40.0



def test_financial_truth_accepts_recent_complete_matching_rpc_proof(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    wallet = "0x" + "a" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    fingerprint = hashlib.sha256(wallet.lower().encode("ascii")).hexdigest()
    hub = {
        "accounts": {
            "polymarket": {
                "balance_usdc": 99999.0,
                "balance_verification": {
                    "status": "verified",
                    "source": "polygon_rpc",
                    "chain": "polygon",
                    "chain_id": 137,
                    "wallet_fingerprint": fingerprint,
                    "observed_at": now.isoformat(),
                    "tokens": {
                        "usdc_bridged": {"status": "verified", "balance": 4.0},
                        "usdc_native": {"status": "verified", "balance": 6.0},
                    },
                },
            }
        }
    }
    path = tmp_path / "hub.json"
    path.write_text(json.dumps(hub))

    result = read_verified_polymarket_balance(path, now=now)

    assert result["verified"] is True
    assert result["balance_usdc"] == 10.0
    assert result["wallet_configured"] is True
    assert result["source"] == "polygon_rpc"


def test_financial_truth_rejects_stale_or_partial_rpc_proof(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    wallet = "0x" + "b" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    fingerprint = hashlib.sha256(wallet.lower().encode("ascii")).hexdigest()
    proof = {
        "status": "verified",
        "source": "polygon_rpc",
        "chain": "polygon",
        "chain_id": 137,
        "wallet_fingerprint": fingerprint,
        "observed_at": (now - timedelta(hours=1)).isoformat(),
        "tokens": {
            "usdc_bridged": {"status": "verified", "balance": 5.0},
            "usdc_native": {"status": "verified", "balance": 5.0},
        },
    }
    path = tmp_path / "hub.json"
    path.write_text(json.dumps({"accounts": {"polymarket": {"balance_verification": proof}}}))

    stale = read_verified_polymarket_balance(path, now=now)
    assert stale["verified"] is False
    assert stale["balance_usdc"] is None

    proof["observed_at"] = now.isoformat()
    proof["tokens"]["usdc_native"]["status"] = "unknown"
    path.write_text(json.dumps({"accounts": {"polymarket": {"balance_verification": proof}}}))
    partial = read_verified_polymarket_balance(path, now=now)
    assert partial["verified"] is False
    assert partial["balance_usdc"] is None


def test_financial_truth_rejects_wallet_mismatch(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    wallet = "0x" + "c" * 40
    other_wallet = "0x" + "d" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    path = tmp_path / "hub.json"
    path.write_text(json.dumps({
        "accounts": {"polymarket": {
            "balance_verification": {
                "status": "verified",
                "source": "polygon_rpc",
                "chain": "polygon",
                "chain_id": 137,
                "wallet_fingerprint": hashlib.sha256(other_wallet.encode()).hexdigest(),
                "observed_at": now.isoformat(),
                "tokens": {
                    "usdc_bridged": {"status": "verified", "balance": 1.0},
                    "usdc_native": {"status": "verified", "balance": 1.0},
                },
            },
        }}
    }))

    result = read_verified_polymarket_balance(path, now=now)

    assert result["verified"] is False
    assert result["balance_usdc"] is None


def test_balance_refresh_records_complete_provenance_without_network(tmp_path, monkeypatch):
    wallet = "0x" + "e" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    hub_path = tmp_path / "hub.json"
    hub_path.write_text(json.dumps({"accounts": {
        "polymarket": {"balance_usdc": 777.0},
        "unrelated": {"balance_usd": 33.0},
    }}))
    monkeypatch.setattr(refresh_balances, "FINANCE_HUB", hub_path)
    monkeypatch.setattr(refresh_balances, "get_chain_id", lambda: 137)
    monkeypatch.setattr(refresh_balances, "get_erc20_balance", lambda address, contract: 3.0 if contract == refresh_balances.USDC_BRIDGED else 7.0)
    monkeypatch.setattr(refresh_balances, "get_native_balance", lambda address: 1.0)

    result = refresh_balances.refresh()
    updated = json.loads(hub_path.read_text())

    assert result["verified"] is True
    assert result["balance_usdc"] == 10.0
    assert updated["accounts"]["polymarket"]["balance_verification"]["status"] == "verified"
    assert updated["accounts"]["polymarket"]["balance_verification"]["source"] == "polygon_rpc"
    assert "wallet_address" not in updated["accounts"]["polymarket"]
    assert updated["accounts"]["unrelated"]["balance_usd"] == 33.0


def test_balance_refresh_partial_rpc_never_promotes_old_balance(tmp_path, monkeypatch):
    wallet = "0x" + "f" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    hub_path = tmp_path / "hub.json"
    hub_path.write_text(json.dumps({"accounts": {"polymarket": {"balance_usdc": 777.0}}}))
    monkeypatch.setattr(refresh_balances, "FINANCE_HUB", hub_path)
    monkeypatch.setattr(refresh_balances, "get_chain_id", lambda: 137)
    monkeypatch.setattr(refresh_balances, "get_erc20_balance", lambda address, contract: 3.0 if contract == refresh_balances.USDC_BRIDGED else None)
    monkeypatch.setattr(refresh_balances, "get_native_balance", lambda address: None)

    result = refresh_balances.refresh()
    updated = json.loads(hub_path.read_text())

    assert result["verified"] is False
    assert result["balance_usdc"] is None
    assert updated["accounts"]["polymarket"]["balance_usdc"] == 777.0
    assert updated["accounts"]["polymarket"]["balance_verification"]["status"] == "partial"
    assert read_verified_polymarket_balance(hub_path)["verified"] is False


def test_financial_truth_rejects_non_polygon_chain_id(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    wallet = "0x" + "9" * 40
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", wallet)
    path = tmp_path / "hub.json"
    path.write_text(json.dumps({
        "accounts": {"polymarket": {
            "balance_verification": {
                "status": "verified",
                "source": "polygon_rpc",
                "chain": "polygon",
                "chain_id": 1,
                "wallet_fingerprint": hashlib.sha256(wallet.encode()).hexdigest(),
                "observed_at": now.isoformat(),
                "tokens": {
                    "usdc_bridged": {"status": "verified", "balance": 2.0},
                    "usdc_native": {"status": "verified", "balance": 3.0},
                },
            },
        }}
    }))

    result = read_verified_polymarket_balance(path, now=now)

    assert result["verified"] is False
    assert result["balance_usdc"] is None


def test_finance_dashboard_does_not_promote_old_hub_values(tmp_path, monkeypatch):
    hub = {
        "accounts": {"polymarket": {"balance_usdc": 999.0}},
        "summary": {"total_liquid_usd": 5000.0, "runway_months": 9.0},
        "credit": {"total_balance": 100.0, "utilization_pct": 5.0},
    }
    (tmp_path / "private_finance_hub.json").write_text(json.dumps(hub))
    monkeypatch.setattr(finance_dashboard, "STATE_DIR", tmp_path)

    pm = finance_dashboard.get_polymarket_status()
    runway = finance_dashboard.get_runway_status()
    credit = finance_dashboard.get_credit_status()

    assert pm["verified"] is False
    assert pm["balance_usdc"] is None
    assert runway["runway_months"] is None
    assert runway["total_liquid"] is None
    assert credit["total_balance"] is None


def test_system_doctor_never_calculates_runway_from_manual_cache():
    doctor = SystemDoctor.__new__(SystemDoctor)
    doctor._sensitive_data = {"wallet_usdc": 1000.0}

    symptoms = doctor.check_financial_runway()

    assert doctor._sensitive_data["runway_months"] == "unknown"
    assert doctor._sensitive_data["monthly_burn"] is None
    assert symptoms[0].symptom == "Financial runway is unverified"


def test_moonshot_prompt_has_no_hardcoded_financial_or_telegram_claims():
    path = Path(__file__).resolve().parents[1] / "autonomous" / "moonshot_loop.py"
    source = path.read_text()

    assert "8214203655" not in source
    assert "8327766663" not in source
    assert "3280" not in source
    assert '"position_value": 98' not in source
    assert "Verified positions: UNKNOWN" in source
    assert "Never infer income from websites" in source



def test_financial_truth_rejects_non_polygon_chain_id(tmp_path):
    now = datetime.now(timezone.utc)
    wallet = "0x" + "9" * 40
    path = tmp_path / "hub.json"
    path.write_text(json.dumps({
        "accounts": {"polymarket": {
            "wallet_address": wallet,
            "balance_verification": {
                "status": "verified",
                "source": "polygon_rpc",
                "chain": "polygon",
                "chain_id": 1,
                "wallet_address": wallet,
                "observed_at": now.isoformat(),
                "tokens": {
                    "usdc_bridged": {"status": "verified", "balance": 2.0},
                    "usdc_native": {"status": "verified", "balance": 3.0},
                },
            },
        }}
    }))

    result = read_verified_polymarket_balance(path, now=now)

    assert result["verified"] is False
    assert result["balance_usdc"] is None



def test_financial_ledger_blocks_unverified_revenue(tmp_path):
    ledger = FinancialLedger(str(tmp_path / "ledger.jsonl"))

    with pytest.raises(ValueError, match="Unverified revenue blocked"):
        ledger.add_revenue(
            component="test",
            action="claimed_income",
            amount=100.0,
            session_id="test",
            metadata={"note": "model estimate only"},
        )

    assert ledger.get_balance()["total_revenue"] == 0.0


def test_financial_ledger_requires_idempotent_verified_evidence(tmp_path):
    ledger = FinancialLedger(str(tmp_path / "ledger.jsonl"))
    evidence = {
        "verification": {
            "status": "verified",
            "source_type": "payment_processor_settlement",
            "evidence_ref": "settlement:test-001",
            "idempotency_key": "settlement:test-001",
            "verified_by": "payment_processor_verifier",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    entry = ledger.add_revenue(
        component="payments",
        action="settlement",
        amount=25.0,
        session_id="test",
        metadata=evidence,
    )

    assert entry.verified is True
    assert ledger.get_balance()["total_revenue"] == 25.0
    assert ledger.verify_integrity() is True

    with pytest.raises(ValueError, match="Duplicate financial evidence"):
        ledger.add_revenue(
            component="payments",
            action="settlement",
            amount=25.0,
            session_id="test",
            metadata=evidence,
        )


def test_financial_ledger_hash_covers_metadata_and_category(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = FinancialLedger(str(path))
    evidence = {
        "verification": {
            "status": "verified",
            "source_type": "invoice_payment",
            "evidence_ref": "invoice:paid-123",
            "idempotency_key": "invoice:paid-123",
            "verified_by": "invoice_payment_verifier",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
    }
    ledger.add_revenue("services", "invoice_paid", 40.0, "test", evidence)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[-1]["metadata"]["customer"] = "tampered"
    path.write_text("\n".join(json.dumps(item) for item in records) + "\n")

    assert ledger.verify_integrity() is False


def test_financial_ledger_excludes_unverified_costs_from_verified_roi(tmp_path):
    ledger = FinancialLedger(str(tmp_path / "ledger.jsonl"))
    ledger.add_cost("ai", "estimated_usage", 5.0, "test")

    balance = ledger.get_balance()

    assert balance["total_costs"] == 0.0
    assert balance["unverified_costs"] == 5.0
    assert balance["verified"] is False


def test_payment_monitor_does_not_promote_partial_rpc_data(tmp_path, monkeypatch):
    from scripts import payment_monitor

    state_path = tmp_path / "payment-monitor.json"
    original = {
        "last_balance": 41.25,
        "last_check": "2026-01-01T00:00:00+00:00",
        "payments": [{"amount": 12.0}],
    }
    state_path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(payment_monitor, "STATE_FILE", state_path)
    values = iter([41.25, None])
    monkeypatch.setattr(payment_monitor, "get_token_balance", lambda *_: next(values))

    result = payment_monitor.main()

    assert result == {"status": "unknown", "balance_usdc": None}
    assert json.loads(state_path.read_text(encoding="utf-8")) == original


def test_payment_monitor_rpc_error_is_unknown_not_zero(monkeypatch):
    from scripts import payment_monitor

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": "unavailable"}}

    monkeypatch.setattr(payment_monitor.requests, "post", lambda *args, **kwargs: Response())
    assert payment_monitor.get_token_balance(payment_monitor.WALLET, payment_monitor.USDC_CONTRACT) is None


def test_ledger_concurrent_appends_preserve_hash_chain(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from audit.ledger import FinancialLedger

    ledger_path = tmp_path / "ledger.jsonl"
    ledger = FinancialLedger(str(ledger_path))

    def append(index):
        return ledger.add_cost("concurrency-test", f"append-{index}", 1.0, "test")

    with ThreadPoolExecutor(max_workers=8) as pool:
        entries = list(pool.map(append, range(32)))

    assert len(entries) == 32
    assert ledger.verify_integrity() is True
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 33
    assert len({row["entry_id"] for row in rows}) == 33
    for previous, current in zip(rows, rows[1:]):
        assert current["previous_hash"] == previous["current_hash"]


def test_ledger_idempotency_is_checked_inside_append_lock(tmp_path):
    from audit.ledger import FinancialLedger

    ledger = FinancialLedger(str(tmp_path / "ledger.jsonl"))
    evidence = {
        "verification": {
            "status": "verified",
            "source_type": "bank_transaction",
            "evidence_ref": "statement-row-123",
            "idempotency_key": "bank:statement-row-123",
            "verified_by": "test",
            "verified_at": "2026-11-22T00:00:00+00:00",
        }
    }
    ledger.add_revenue("test", "settlement", 5.0, "session", evidence)
    try:
        ledger.add_revenue("test", "settlement", 5.0, "session", evidence)
    except ValueError as exc:
        assert "Duplicate financial evidence" in str(exc)
    else:
        raise AssertionError("duplicate evidence must be rejected")
    assert len(ledger.get_entries()) == 1
    assert ledger.verify_integrity() is True


def test_finance_hub_concurrent_account_updates_do_not_lose_data(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from finance.hub_store import load_hub, update_account

    path = tmp_path / "private_finance_hub.json"

    def update(index):
        return update_account(
            path,
            f"account-{index}",
            {"observed_value": index},
            top_level_updates={"writer_timestamp": str(index)},
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(update, range(24)))

    hub = load_hub(path)
    assert len(hub["accounts"]) == 24
    for index in range(24):
        assert hub["accounts"][f"account-{index}"]["observed_value"] == index


def test_aggregator_merges_delta_into_latest_finance_hub(tmp_path, monkeypatch):
    from finance.aggregators import free_stack
    from finance.hub_store import update_account

    path = tmp_path / "private_finance_hub.json"
    monkeypatch.setattr(free_stack, "HUB_PATH", path)
    monkeypatch.setenv("POLYMARKET_FUNDER_ADDRESS", "0x" + "1" * 40)
    aggregator = free_stack.FreeAggregator()
    update_account(path, "other", {"newer_value": 99})

    observed = "2026-11-22T00:00:00+00:00"
    monkeypatch.setattr(
        aggregator,
        "fetch_polymarket",
        lambda wallet: {
            "status": "verified",
            "balance_usdc": 10.0,
            "balance_matic": None,
            "balance_verification": {"observed_at": observed},
        },
    )

    aggregator.refresh_all()
    hub = free_stack.load_hub(path)
    assert hub["accounts"]["other"]["newer_value"] == 99
    assert hub["accounts"]["polymarket"]["balance_usdc"] == 10.0
