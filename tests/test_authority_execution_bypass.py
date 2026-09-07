from ai.decision.action_kernel import ActionDecision
from ai.factory.authority_gateway import FactoryAuthorityGateway


class FakeRuntime:
    def __init__(self):
        self.development_tracker = object()
        self.improvement_approval = object()
        self.improvement_queue = object()
        self.artifact_registry = object()
        self.development_pipeline = object()
        self.execute_calls = []
        self.autonomous_execute_called = False

    def report_autonomy_state(self, objective, decision):
        return {"objective": objective, "decision": decision, "status": "recorded"}

    def execute(self, objective):
        self.execute_calls.append(objective)
        return {"success": True, "objective": objective}

    def autonomous_execute(self, objective):
        self.autonomous_execute_called = True
        raise AssertionError("legacy autonomous wrapper must not be called")


class FakeJournal:
    def __init__(self):
        self.records = []

    def record(self, execution_id, status, payload=None):
        self.records.append((execution_id, status, payload))

    def interrupted(self):
        return []


def ready_inference(monkeypatch):
    class ReadyInference:
        def evaluate(self, objective):
            return {"objective": objective, "decision": {
                "status": "CAPABILITIES_AVAILABLE",
                "action": "activate_existing_factory",
            }}
    monkeypatch.setattr(
        "ai.factory.authority_gateway.FactoryCapabilityRequirementInference",
        ReadyInference,
    )


def test_authority_execution_uses_canonical_convergence(monkeypatch):
    ready_inference(monkeypatch)
    runtime = FakeRuntime()
    gateway = FactoryAuthorityGateway(runtime, FakeJournal())
    result = gateway.execute_autonomous("test objective")
    assert result["status"] == "verified"
    assert result["verified"] is True
    assert result["execution"]["success"] is True
    assert runtime.execute_calls == ["test objective"]
    assert runtime.autonomous_execute_called is False


def test_authority_convergence_receives_complete_policy_evidence(monkeypatch):
    ready_inference(monkeypatch)

    class RecordingConvergence:
        def __init__(self):
            self.evaluated = None
            self.executed = None

        def evaluate(self, **kwargs):
            self.evaluated = kwargs
            return ActionDecision(True, "test approval", 1.0, 0.0, 0.0,
                                  ("test",), kwargs["evidence"])

        def execute(self, **kwargs):
            self.executed = kwargs
            result = kwargs["executor"](kwargs["decision"])
            assert kwargs["verifier"](result, kwargs["decision"])
            return {"status": "verified", "verified": True, "result": result,
                    "decision": kwargs["decision"].as_dict()}

    runtime = FakeRuntime()
    gateway = FactoryAuthorityGateway(runtime, FakeJournal())
    convergence = RecordingConvergence()
    gateway.convergence = convergence
    result = gateway.execute_autonomous("convergence objective")

    assert result["status"] == "verified"
    assert convergence.evaluated["confidence"] == 1.0
    assert convergence.evaluated["risk_score"] == 0.0
    assert convergence.evaluated["max_risk"] == 0.0
    assert convergence.evaluated["min_confidence"] == 1.0
    assert convergence.executed is not None
