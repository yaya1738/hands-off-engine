from ai.factory.authority_gateway import FactoryAuthorityGateway


class FakeRuntime:
    def __init__(self):
        self.development_tracker = object()
        self.improvement_approval = object()
        self.improvement_queue = object()
        self.artifact_registry = object()
        self.development_pipeline = object()
        self.autonomous_execute_called = False

    def report_autonomy_state(self, objective, decision):
        return {"objective": objective, "decision": decision, "status": "recorded"}

    def execute(self, objective):
        return {"success": True, "objective": objective}

    def autonomous_execute(self, objective):
        self.autonomous_execute_called = True
        raise AssertionError("authority gateway must not delegate to legacy runtime autonomous_execute")


class FakeJournal:
    def __init__(self):
        self.records = []

    def record(self, execution_id, status, payload=None):
        self.records.append((execution_id, status, payload))

    def interrupted(self):
        return []


def test_authority_execution_does_not_delegate_to_legacy_runtime_wrapper(monkeypatch):
    class ReadyGateway:
        def evaluate(self, objective):
            return {"activation": {"decision": {"status": "READY"}}}

    monkeypatch.setattr(
        "ai.factory.authority_gateway.FactoryRuntimeAutonomyGateway",
        ReadyGateway,
    )

    runtime = FakeRuntime()
    gateway = FactoryAuthorityGateway(runtime, FakeJournal())

    result = gateway.execute_autonomous("test objective")

    assert result["execution"]["success"] is True
    assert runtime.autonomous_execute_called is False
