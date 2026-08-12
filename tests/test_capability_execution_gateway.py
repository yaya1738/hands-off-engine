import pytest

from ai.factory.capability_execution_gateway import (
    FactoryCapabilityExecutionGateway,
)


class Audit:
    def __init__(self):
        self.records = []

    def record_decision(self, value):
        self.records.append(("decision", value))

    def record_action(self, value):
        self.records.append(("action", value))

    def record_outcome(self, value):
        self.records.append(("outcome", value))


class Router:
    def route(self, decision):
        return {"action": "continue", "decision": decision["decision"]}

    def execute(self, routed):
        return {"executed": True, "action": routed["action"]}


class Handoff:
    def create_handoff(self, decision):
        return {"created": True, "handoff": decision}

    def validate_handoff(self):
        return {"valid": True}


class Execution:
    def __init__(self):
        self.created = []

    def create_execution(self, execution_id, execution):
        self.created.append((execution_id, execution))

    def start_execution(self, execution_id):
        return {"started": True, "execution_id": execution_id}

    def complete_execution(self, execution_id):
        return {"completed": True, "execution_id": execution_id}

    def track_execution(self, execution_id):
        return {"tracked": True, "execution_id": execution_id}


class Integrity:
    def check_runtime(self, runtime):
        return {"healthy": True}


class Learning:
    def __init__(self):
        self.experiences = []
        self.outcomes = []

    def record_experience(self, value):
        self.experiences.append(value)

    def analyze_outcome(self, value):
        self.outcomes.append(value)


class Runtime:
    def __init__(self):
        self.action_router = Router()
        self.execution_handoff = Handoff()
        self.execution = Execution()
        self.integrity_checker = Integrity()
        self.learning = Learning()
        self.action_audit = Audit()


def test_bounded_capability_completes_authoritative_path():
    runtime = Runtime()
    gateway = FactoryCapabilityExecutionGateway(runtime)

    result = gateway.submit(
        {
            "capability": "factory_test",
            "action": "CONTINUE",
            "parameters": {"value": 1},
        }
    )

    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert runtime.execution.created
    assert runtime.learning.experiences
    assert runtime.learning.outcomes
    assert [item[0] for item in runtime.action_audit.records] == [
        "decision",
        "action",
        "outcome",
    ]


def test_capability_request_rejects_unbounded_fields():
    gateway = FactoryCapabilityExecutionGateway(Runtime())

    with pytest.raises(ValueError, match="unsupported fields"):
        gateway.submit(
            {
                "capability": "factory_test",
                "action": "CONTINUE",
                "callable": "arbitrary_python",
            }
        )
