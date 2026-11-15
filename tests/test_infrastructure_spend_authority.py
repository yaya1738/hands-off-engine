import inspect
from types import SimpleNamespace

import infrastructure.auto_provisioner as provisioner_module
from infrastructure.auto_provisioner import AutoProvisioner
from infrastructure.infra_types import InfrastructureBudget, InstanceSize, ServerRole
from infrastructure.autonomous_infra_manager import AutonomousInfraManager
import autonomous.unified_system as unified


class FakeCloud:
    def __init__(self):
        self.create_calls = 0

    def create_server(self, request):
        self.create_calls += 1
        return True, None, "created"


def _provisioner(monkeypatch, tmp_path, **kwargs):
    api = FakeCloud()
    monkeypatch.setattr(provisioner_module, "get_best_available_provider", lambda: (api, "mock"))
    monkeypatch.setattr(provisioner_module, "HARDWARE_MONITORING_AVAILABLE", False)
    instance = AutoProvisioner(state_path=tmp_path, **kwargs)
    return instance, api


def test_auto_provisioner_defaults_to_no_paid_actions(monkeypatch, tmp_path):
    instance, api = _provisioner(monkeypatch, tmp_path)
    assert instance.dry_run is True
    assert instance.allow_paid_actions is False
    assert instance.auto_execute_enabled is False
    assert instance.budget.monthly_limit == 0.0
    ok, server, message = instance.provision_new_server(ServerRole.GENERAL, InstanceSize.SMALL)
    assert ok is True
    assert "DRY RUN" in message
    assert api.create_calls == 0


def test_live_provisioning_requires_explicit_paid_authority(monkeypatch, tmp_path):
    instance, api = _provisioner(monkeypatch, tmp_path, dry_run=False)
    ok, server, message = instance.provision_new_server(ServerRole.GENERAL, InstanceSize.SMALL)
    assert ok is False
    assert "disabled" in message
    assert api.create_calls == 0


def test_explicit_paid_authority_still_obeys_zero_budget(monkeypatch, tmp_path):
    budget = InfrastructureBudget(monthly_limit=0.0)
    instance, api = _provisioner(
        monkeypatch, tmp_path, dry_run=False, allow_paid_actions=True, budget=budget
    )
    ok, server, message = instance.provision_new_server(ServerRole.GENERAL, InstanceSize.SMALL)
    assert ok is False
    assert "budget exceeded" in message.lower()
    assert api.create_calls == 0


def test_autoprovisioner_does_not_auto_execute_without_second_opt_in(monkeypatch, tmp_path):
    instance, _ = _provisioner(
        monkeypatch, tmp_path, dry_run=False, allow_paid_actions=True, auto_execute_enabled=False,
        budget=InfrastructureBudget(monthly_limit=500.0),
    )
    decision = SimpleNamespace(
        auto_approved=True, requires_approval=False, action="upgrade_server",
        execution_result="", executed=False,
    )
    instance.refresh_servers = lambda: None
    instance._check_horizontal_scaling = lambda _health: [decision]
    instance._check_idle_servers = lambda: []
    instance._enforce_budget = lambda _decisions: None
    instance._save_state = lambda: None
    instance._log_decisions = lambda _decisions: None
    calls = []
    instance._execute_decision = lambda _decision: calls.append(1) or True
    result = instance.analyze_and_scale()
    assert calls == []
    assert result[0].requires_approval is True
    assert result[0].auto_approved is False
    assert "disabled" in result[0].execution_result


def test_infrastructure_manager_defaults_are_non_spending():
    defaults = inspect.signature(AutonomousInfraManager.__init__).parameters
    assert defaults["budget_monthly"].default == 0.0
    assert defaults["auto_provision"].default is False
    assert defaults["auto_upgrade"].default is False
    assert defaults["auto_scale"].default is False
    assert defaults["dry_run"].default is True
    assert defaults["allow_paid_actions"].default is False


def test_unified_system_defaults_are_non_spending():
    defaults = inspect.signature(unified.UnifiedAutonomousSystem.__init__).parameters
    assert defaults["infrastructure_budget"].default == 0.0
    assert defaults["auto_provision"].default is False
    assert defaults["auto_upgrade"].default is False
    assert defaults["dry_run"].default is True
    assert defaults["allow_paid_actions"].default is False


def test_unified_critical_health_queues_instead_of_auto_provisioning(monkeypatch):
    system = object.__new__(unified.UnifiedAutonomousSystem)
    system.auto_provision = True
    system.auto_upgrade = True
    system.allow_paid_actions = False
    system._within_auto_approve_budget = lambda: True
    system._create_infra_decision = lambda **kwargs: {
        "id": "infra-test", "action": kwargs["action"], "reason": kwargs["reason"],
        "auto_approve": kwargs["auto_approve"], "executed": False,
    }
    queued, executed = [], []
    system._queue_infra_for_approval = lambda decision: queued.append(decision)
    system._execute_infra_decision = lambda decision: executed.append(decision)
    health = SimpleNamespace(overall_status=unified.HealthStatus.CRITICAL, overall_score=10)
    decisions = system._make_infrastructure_decisions(health)
    assert len(decisions) == 1
    assert len(queued) == 1
    assert executed == []
    assert decisions[0]["auto_approve"] is False


def test_unified_cli_requires_explicit_enable_spend(monkeypatch):
    calls = []
    monkeypatch.setattr(unified, "start_live_system", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.argv", ["unified_system.py"])
    unified.main()
    assert calls[-1]["budget"] == 0.0
    assert calls[-1]["auto_provision"] is False
    assert calls[-1]["auto_upgrade"] is False
    assert calls[-1]["dry_run"] is True
    assert calls[-1]["allow_paid_actions"] is False


def test_unified_cli_explicit_spend_flag_is_visible_and_bounded(monkeypatch):
    calls = []
    monkeypatch.setattr(unified, "start_live_system", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.argv", ["unified_system.py", "--enable-spend", "--budget", "35"])
    unified.main()
    assert calls[-1]["budget"] == 35.0
    assert calls[-1]["auto_provision"] is True
    assert calls[-1]["auto_upgrade"] is True
    assert calls[-1]["dry_run"] is False
    assert calls[-1]["allow_paid_actions"] is True
