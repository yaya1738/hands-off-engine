from unittest.mock import patch

from ai.factory.authority_gateway import FactoryAuthorityGateway


def test_authority_gateway_does_not_call_missing_runtime_execute():
    class Runtime:
        def report_autonomy_state(self, objective, decision):
            return {"status": "recorded"}

        def execute(self, objective):
            raise AssertionError("legacy/missing runtime.execute must not be used")

    gateway = FactoryAuthorityGateway.__new__(FactoryAuthorityGateway)
    gateway.runtime = Runtime()

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
