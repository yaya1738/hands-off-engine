from ai.factory.autonomy_manager import FactoryAutonomyManager
from ai.factory.authority_gateway import FactoryAuthorityGateway


class FakeJournal:
    def __init__(self):
        self.records = []

    def record(self, execution_id, status, payload=None):
        self.records.append((execution_id, status, payload))

    def interrupted(self):
        return []


class FakeRuntime:
    def __init__(self):
        self.legacy_called = False
        self.autonomous_called = False
        self.executed = False
        self.development_tracker = object()
        self.improvement_approval = object()
        self.improvement_queue = object()
        self.artifact_registry = object()
        self.development_pipeline = object()

    def component_inventory(self):
        return {"component_count": 1}

    def autonomous_execute(self, objective):
        self.autonomous_called = True
        self.executed = True
        self.legacy_called = True
        raise AssertionError("authority gateway must not delegate to legacy runtime autonomous_execute")

    def report_autonomy_state(self, objective, decision):
        return {
            "objective": objective,
            "decision": decision,
            "status": "recorded",
        }

    def execute(self, objective):
        self.executed = True
        return {"success": True, "objective": objective}


class FakeAuthority:
    def __init__(self):
        self.objectives = []

    def execute_autonomous(self, objective):
        self.objectives.append(objective)
        return {"status": "executed", "objective": objective}


def test_execute_routes_through_authority_gateway_without_legacy_bypass():
    runtime = FakeRuntime()
    authority = FakeAuthority()
    manager = FactoryAutonomyManager(runtime)
    manager._authority_gateway = authority

    result = manager.execute("migrate execution authority")

    assert result["execution"] == {
        "status": "executed",
        "objective": "migrate execution authority",
    }
    assert authority.objectives == ["migrate execution authority"]
    assert runtime.legacy_called is False


def test_authority_gateway_routes_ready_execution_through_runtime(monkeypatch):
    class ReadyGateway:
        def evaluate(self, objective):
            return {
                "activation": {
                    "decision": {
                        "status": "READY",
                        "classification": "factory_ready",
                    }
                }
            }

    monkeypatch.setattr(
        "ai.factory.authority_gateway.FactoryRuntimeAutonomyGateway",
        ReadyGateway,
    )

    runtime = FakeRuntime()
    journal = FakeJournal()
    gateway = FactoryAuthorityGateway.__new__(FactoryAuthorityGateway)
    gateway.runtime = runtime
    gateway.execution_journal = journal

    result = gateway.execute_autonomous("preserve autonomous readiness")

    assert result == {
        "decision": {
            "status": "READY",
            "classification": "factory_ready",
        },
        "execution": {
            "success": True,
            "objective": "preserve autonomous readiness",
        },
    }
    assert runtime.legacy_called is False
    assert runtime.executed is True
    assert [status for _, status, _ in journal.records] == ["STARTED", "COMPLETED"]
