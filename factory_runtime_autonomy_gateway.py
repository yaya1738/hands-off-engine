from factory_capability_requirement_inference import FactoryCapabilityRequirementInference
from factory_autonomous_controller import FactoryAutonomousController


class FactoryRuntimeAutonomyGateway:
    """Compatibility boundary for capability evaluation and governed execution.

    Evaluation must be pure. Consequential activation belongs to the authority
    gateway/convergence lifecycle, never to an apparently read-only evaluate call.
    """

    def __init__(self):
        self.requirements = FactoryCapabilityRequirementInference()
        self.controller = FactoryAutonomousController()

    def evaluate(self, objective):
        return self.requirements.evaluate(objective)

    def execute(self, objective):
        return self.controller.evaluate_and_execute(objective)
