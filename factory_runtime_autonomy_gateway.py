from factory_capability_requirement_inference import (
    FactoryCapabilityRequirementInference,
)
from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryRuntimeAutonomyGateway:
    """Compatibility adapter separating readiness evaluation from execution."""

    def __init__(self, runtime=None):
        self.authority = FactoryAuthorityGateway(runtime=runtime)
        self.requirements = FactoryCapabilityRequirementInference()

    def evaluate(self, objective):
        """Evaluate readiness only; never execute the objective."""
        capability_report = self.requirements.evaluate(objective)
        decision = capability_report.get("decision", {})
        ready = decision.get("action") == "activate_existing_factory"

        return {
            "objective": objective,
            "capability_evaluation": capability_report,
            "activation": {
                "status": "READY" if ready else "BLOCKED",
                "decision": decision,
            },
        }

    def execute(self, objective):
        """Execute only after the caller has completed readiness evaluation."""
        return self.authority.execute(objective)
