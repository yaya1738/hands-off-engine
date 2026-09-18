import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.factory_execution_adapter import execute_factory_command


def test_factory_live_requires_approval():
    result = execute_factory_command(
        {"id": "fx-1", "mode": "LIVE", "objective": "inspect runtime"},
        execution_gate=True,
    )
    assert result["status"] == "approval_required"


def test_factory_live_requires_explicit_executor_gate():
    result = execute_factory_command(
        {"id": "fx-2", "mode": "LIVE", "approval_status": "approved", "objective": "inspect runtime"},
        execution_gate=False,
    )
    assert result["status"] == "awaiting_executor_gate"


def test_factory_dryrun_never_requires_execution_gate():
    result = execute_factory_command(
        {"id": "fx-3", "mode": "DRYRUN", "objective": "inspect runtime"},
        execution_gate=False,
    )
    assert result["status"] == "dryrun_only"


def test_factory_missing_objective_fails_closed():
    result = execute_factory_command(
        {"id": "fx-4", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=True,
    )
    assert result["status"] == "rejected"


def test_factory_live_preserves_correlation(monkeypatch):
    import types
    import sys

    class FakeGateway:
        def execute_autonomous(self, objective, idempotency_key=None):
            assert objective == "inspect runtime"
            assert idempotency_key == "fx-5"
            return {"decision": "accepted"}

    fake_module = types.ModuleType("ai.factory.authority_gateway")
    fake_module.FactoryAuthorityGateway = FakeGateway
    monkeypatch.setitem(sys.modules, "ai.factory.authority_gateway", fake_module)

    result = execute_factory_command(
        {
            "id": "fx-5",
            "mode": "LIVE",
            "approval_status": "approved",
            "objective": "inspect runtime",
            "reply_to": "mailbox-42",
        },
        execution_gate=True,
    )

    assert result["status"] == "completed"
    assert result["command_id"] == "fx-5"
    assert result["correlation_id"] == "mailbox-42"
    assert result["factory"] == {"decision": "accepted"}


def test_system_listener_routes_approved_factory_command(monkeypatch):
    import scripts.system_listener_inline as listener

    calls = {}

    def fake_execute(command, execution_gate=False):
        calls["command"] = command
        calls["execution_gate"] = execution_gate
        return {
            "status": "completed",
            "command_id": command["id"],
            "correlation_id": command["correlation_id"],
            "factory": {"status": "verified"},
        }

    monkeypatch.setattr(listener, "execute_factory_command", fake_execute)

    result = listener.process_command({
        "id": "fx-listener-1",
        "action": "execute",
        "target": "factory",
        "mode": "LIVE",
        "approval_status": "approved",
        "objective": "inspect runtime",
        "reply_to": "mailbox-77",
        "payload": {"objective": "inspect runtime"},
    })

    assert result["command_status"] == "completed"
    assert result["execution_result"]["correlation_id"] == "mailbox-77"
    assert calls["execution_gate"] is True
    assert calls["command"]["objective"] == "inspect runtime"
