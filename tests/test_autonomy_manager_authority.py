from ai.factory.autonomy_manager import FactoryAutonomyManager
from ai.factory.authority_gateway import FactoryAuthorityGateway


class FakeJournal:
    def __init__(self):
        self.records = []

    def record(self, execution_id, status, payload=None):
        self.records.append((execution_id, status, payload))


class FakeRuntime:
    def __init__(self):
        self.legacy_called = False
        self.autonomous_called = False
        self.executed = False

    def component_inventory(self):
        return {"component_count": 1}

    def autonomous_execute(self, objective):
        self.autonomous_called = True
        self.executed = True
        return {"status": "executed", "objective": objective}


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


def test_authority_gateway_routes_autonomous_execution_through_runtime_gate():
    runtime = FakeRuntime()
    journal = FakeJournal()
    gateway = FactoryAuthorityGateway.__new__(FactoryAuthorityGateway)
    gateway.runtime = runtime
    gateway.execution_journal = journal

    result = gateway.execute_autonomous("preserve autonomous readiness")

    assert result == {
        "status": "executed",
        "objective": "preserve autonomous readiness",
    }
    assert runtime.autonomous_called is True
    assert runtime.executed is True
    assert [status for _, status, _ in journal.records] == ["STARTED", "COMPLETED"]
