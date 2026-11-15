import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.factory_execution_adapter import execute_factory_command
from scripts.command_approval import command_fingerprint
from datetime import datetime, timezone
import json


def _approved(command, tmp_path):
    command = dict(command)
    command.setdefault("source", "test")
    command.setdefault("action", "execute")
    command.setdefault("target", "factory")
    command.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    command.setdefault("priority", 5)
    command.setdefault("sync", False)
    command.setdefault("timeout_seconds", 300)
    command.setdefault("queued_at", datetime.now(timezone.utc).isoformat())
    command["approval_status"] = "approved"
    fingerprint = command_fingerprint(command)
    command["approval_fingerprint"] = fingerprint
    approval_file = tmp_path / "approval_queue.json"
    approval_file.write_text(json.dumps({"pending": [], "approved": [{"id": command["id"],
        "approved_at": datetime.now(timezone.utc).isoformat(), "fingerprint": fingerprint}], "rejected": []}))
    return command, approval_file


def test_factory_live_requires_approval():
    result = execute_factory_command(
        {"id": "fx-1", "mode": "LIVE", "objective": "inspect runtime"},
        execution_gate=True,
    )
    assert result["status"] == "approval_required"


def test_factory_live_requires_explicit_executor_gate(tmp_path):
    command, approval_file = _approved({"id": "fx-2", "mode": "LIVE", "objective": "inspect runtime"}, tmp_path)
    result = execute_factory_command(command, execution_gate=False, approval_file=approval_file)
    assert result["status"] == "awaiting_executor_gate"


def test_factory_dryrun_never_requires_execution_gate():
    result = execute_factory_command(
        {"id": "fx-3", "mode": "DRYRUN", "objective": "inspect runtime"},
        execution_gate=False,
    )
    assert result["status"] == "dryrun_only"


def test_factory_missing_objective_fails_closed(tmp_path):
    command, approval_file = _approved({"id": "fx-4", "mode": "LIVE"}, tmp_path)
    result = execute_factory_command(command, execution_gate=True, approval_file=approval_file)
    assert result["status"] == "rejected"


def test_factory_live_preserves_correlation(monkeypatch, tmp_path):
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

    command, approval_file = _approved({
        "id": "fx-5", "mode": "LIVE", "objective": "inspect runtime",
        "reply_to": "mailbox-42",
    }, tmp_path)
    result = execute_factory_command(command, execution_gate=True, approval_file=approval_file)

    assert result["status"] == "completed"
    assert result["command_id"] == "fx-5"
    assert result["correlation_id"] == "mailbox-42"
    assert result["factory"] == {"decision": "accepted"}


def test_system_listener_routes_approved_factory_command(monkeypatch, tmp_path):
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

    command, approval_file = _approved({
        "id": "fx-listener-1", "action": "execute", "target": "factory",
        "mode": "LIVE", "objective": "inspect runtime", "reply_to": "mailbox-77",
        "payload": {"objective": "inspect runtime"},
    }, tmp_path)
    monkeypatch.setattr(listener, "APPROVAL_FILE", approval_file)
    result = listener.process_command(command)

    assert result["command_status"] == "completed"
    assert result["execution_result"]["correlation_id"] == "mailbox-77"
    assert calls["execution_gate"] is True
    assert calls["command"]["objective"] == "inspect runtime"


def test_system_listener_rejects_factory_command_without_objective(monkeypatch):
    import scripts.system_listener_inline as listener

    calls = []

    def fake_execute(command, execution_gate=False):
        calls.append(command)
        return {"status": "completed"}

    monkeypatch.setattr(listener, "execute_factory_command", fake_execute)

    result = listener.process_command({
        "id": "fx-listener-missing-objective",
        "action": "execute",
        "target": "factory",
        "mode": "LIVE",
        "approval_status": "approved",
        "payload": {"action": "factory_execute"},
    })

    assert result["command_status"] == "awaiting_approval"
    assert calls == []


def test_factory_adapter_preserves_terminal_status(monkeypatch, tmp_path):
    import types
    import sys

    class FakeGateway:
        def execute_autonomous(self, objective, idempotency_key=None):
            return {"status": "blocked", "execution_id": "ex-1"}

    fake_module = types.ModuleType("ai.factory.authority_gateway")
    fake_module.FactoryAuthorityGateway = FakeGateway
    monkeypatch.setitem(sys.modules, "ai.factory.authority_gateway", fake_module)

    command, approval_file = _approved({
        "id": "fx-status-1", "mode": "LIVE", "objective": "inspect runtime",
    }, tmp_path)
    result = execute_factory_command(command, execution_gate=True, approval_file=approval_file)

    assert result["status"] == "blocked"
    assert result["factory"]["status"] == "blocked"


def test_factory_adapter_maps_verified_to_completed(monkeypatch, tmp_path):
    import types
    import sys

    class FakeGateway:
        def execute_autonomous(self, objective, idempotency_key=None):
            return {"status": "verified", "execution_id": "ex-verified"}

    fake_module = types.ModuleType("ai.factory.authority_gateway")
    fake_module.FactoryAuthorityGateway = FakeGateway
    monkeypatch.setitem(sys.modules, "ai.factory.authority_gateway", fake_module)

    command, approval_file = _approved({
        "id": "fx-status-verified", "mode": "LIVE", "objective": "inspect runtime",
    }, tmp_path)
    result = execute_factory_command(command, execution_gate=True, approval_file=approval_file)

    assert result["status"] == "completed"
    assert result["factory"]["status"] == "verified"


def test_factory_adapter_rejects_action_as_objective(monkeypatch, tmp_path):
    import types
    import sys

    class ExplodingGateway:
        def __init__(self):
            raise AssertionError("Gateway must not be reached")

    fake_module = types.ModuleType("ai.factory.authority_gateway")
    fake_module.FactoryAuthorityGateway = ExplodingGateway
    monkeypatch.setitem(sys.modules, "ai.factory.authority_gateway", fake_module)

    command, approval_file = _approved({
        "id": "fx-missing-objective", "mode": "LIVE",
        "payload": {"action": "factory_execute"},
    }, tmp_path)
    result = execute_factory_command(command, execution_gate=True, approval_file=approval_file)

    assert result["status"] == "rejected"
    assert result["reason"] == "missing Factory objective"
