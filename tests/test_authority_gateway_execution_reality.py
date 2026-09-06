from unittest.mock import patch

from ai.factory.authority_gateway import FactoryAuthorityGateway


class Journal:
    def __init__(self):
        self.records = []

    def record(self, *args):
        self.records.append(args)


def test_authority_gateway_does_not_call_missing_runtime_execute():
    class Runtime:
        def report_autonomy_state(self, objective, decision):
            return {"status": "recorded"}

        def execute(self, objective):
            raise AssertionError("legacy/missing runtime.execute must not be used")

    gateway = FactoryAuthorityGateway.__new__(FactoryAuthorityGateway)
    gateway.runtime = Runtime()
    gateway.execution_journal = Journal()

    evaluation = {
        "activation": {
            "decision": {"status": "PASS"},
            "status": "ACTIVATED",
        }
    }

    with patch(
        "factory_runtime_autonomy_gateway.FactoryRuntimeAutonomyGateway.evaluate",
        return_value=evaluation,
    ):
        result = gateway.execute_autonomous("test objective")

    assert result["status"] == "activated"
    assert result["execution"]["activation"]["status"] == "ACTIVATED"
    assert result["evidence"]["activation_observed"] is True
    assert result["evidence"]["verification_observed"] is True
