import inspect
from types import SimpleNamespace

from hardware.hardware_decision_engine import (
    HardwareDecisionEngine,
    ComponentType,
)
import autonomous.unified_system as unified


def test_emergency_memory_cleanup_requires_auto_execution_opt_in():
    engine = object.__new__(HardwareDecisionEngine)
    engine.auto_execute_enabled = False
    comp_health = SimpleNamespace(component=ComponentType.MEMORY)
    metrics = SimpleNamespace(
        node_id="node-test",
        memory=SimpleNamespace(available_gb=0.2),
    )
    decisions = engine._handle_critical_component(comp_health, metrics, trading_ok=False)
    assert len(decisions) == 1
    assert decisions[0].auto_executed is False
    assert decisions[0].requires_approval is True


def test_emergency_disk_cleanup_requires_auto_execution_opt_in():
    engine = object.__new__(HardwareDecisionEngine)
    engine.auto_execute_enabled = False
    comp_health = SimpleNamespace(component=ComponentType.DISK)
    metrics = SimpleNamespace(
        node_id="node-test",
        disks=[SimpleNamespace(usage_percent=99.0, mount_point="/data")],
    )
    decisions = engine._handle_critical_component(comp_health, metrics, trading_ok=False)
    assert len(decisions) == 1
    assert decisions[0].auto_executed is False
    assert decisions[0].requires_approval is True


def test_disk_cleanup_fails_closed_without_deleting_files():
    engine = object.__new__(HardwareDecisionEngine)
    decision = SimpleNamespace(outcome="")
    assert engine._execute_disk_cleanup(decision) is False
    assert "no files were deleted" in decision.outcome


def test_thermal_mitigation_fails_closed_without_actuator():
    engine = object.__new__(HardwareDecisionEngine)
    decision = SimpleNamespace(outcome="")
    assert engine._execute_thermal_mitigation(decision) is False
    assert "not configured" in decision.outcome


def test_unified_hardware_auto_actions_default_off():
    params = inspect.signature(unified.UnifiedAutonomousSystem.__init__).parameters
    assert params["auto_hardware_actions"].default is False


def test_unified_system_only_auto_approves_successfully_executed_hardware():
    system = object.__new__(unified.UnifiedAutonomousSystem)
    pending = SimpleNamespace(executed=False, success=False)
    assert system._can_auto_approve_hw_decision(pending, health=None) is False
    pending.executed = True
    pending.success = True
    assert system._can_auto_approve_hw_decision(pending, health=None) is True


def test_unified_approval_queue_calls_hardware_engine_and_records_result():
    system = object.__new__(unified.UnifiedAutonomousSystem)
    decision = SimpleNamespace(
        decision_id="hw-1", executed=False, success=False, outcome="",
    )
    class Engine:
        pending_decisions = [decision]
        def approve_decision(self, decision_id):
            assert decision_id == "hw-1"
            decision.executed = True
            decision.success = True
            decision.outcome = "Memory cleanup completed"
            return True
    class Queue:
        def __init__(self):
            self.data = {"approved": [{
                "executed": False,
                "proposed_action": {"type": "hardware_decision", "decision_id": "hw-1"},
            }]}
        def _load_queue(self):
            return self.data
        def _save_queue(self, data):
            self.data = data
    system.hw_decision_engine = Engine()
    system.approval_queue = Queue()
    system._process_approved_actions()
    change = system.approval_queue.data["approved"][0]
    assert change["executed"] is True
    assert change["execution_success"] is True
    assert change["execution_result"] == "Memory cleanup completed"


def test_unified_approval_queue_does_not_mark_missing_hardware_action_executed():
    system = object.__new__(unified.UnifiedAutonomousSystem)
    class Engine:
        pending_decisions = []
        def approve_decision(self, decision_id):
            raise AssertionError("must not execute a missing decision")
    class Queue:
        def __init__(self):
            self.data = {"approved": [{
                "executed": False,
                "proposed_action": {"type": "hardware_decision", "decision_id": "missing"},
            }]}
        def _load_queue(self):
            return self.data
        def _save_queue(self, data):
            self.data = data
    system.hw_decision_engine = Engine()
    system.approval_queue = Queue()
    system._process_approved_actions()
    change = system.approval_queue.data["approved"][0]
    assert change["executed"] is False
    assert "No matching" in change["execution_error"]

def test_unified_cli_requires_hardware_auto_action_opt_in(monkeypatch):
    calls = []
    monkeypatch.setattr(unified, "start_live_system", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.argv", ["unified_system.py"])
    unified.main()
    assert calls[-1]["auto_hardware_actions"] is False

    monkeypatch.setattr(
        "sys.argv",
        ["unified_system.py", "--enable-hardware-auto-actions"],
    )
    unified.main()
    assert calls[-1]["auto_hardware_actions"] is True
    assert calls[-1]["allow_paid_actions"] is False
    assert calls[-1]["dry_run"] is True
