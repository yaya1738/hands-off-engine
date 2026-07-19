import json
from datetime import datetime, timezone

from factory_autonomous_integration_controller import (
    FactoryAutonomousIntegrationController
)

from factory_autonomous_integration_evaluator import (
    FactoryAutonomousIntegrationEvaluator
)


class FactoryAutonomousActivationController:

    def __init__(self):
        self.controller = FactoryAutonomousIntegrationController()
        self.evaluator = FactoryAutonomousIntegrationEvaluator()


    def activate(self, goal):

        controller_result = self.controller.execute(goal)

        evaluation = self.evaluator.evaluate(
            controller_result
        )

        if evaluation["status"] == "PASS":

            lifecycle = (
                controller_result
            )

            return {
                "status": "ACTIVATED",
                "decision": evaluation,
                "lifecycle": lifecycle
            }


        if evaluation["status"] == "BUILD_REQUIRED":

            return {
                "status": "CONSTRUCTION_REQUIRED",
                "decision": evaluation,
                "construction": controller_result
            }


        return {
            "status": "BLOCKED",
            "decision": evaluation
        }



def run():

    activation = FactoryAutonomousActivationController()

    return {
        "timestamp":
            datetime.now(timezone.utc).isoformat(),

        "component":
            "factory_autonomous_activation_controller",

        "result":
            activation.activate(
                "autonomous authority lifecycle execution"
            )
    }


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2
        )
    )
