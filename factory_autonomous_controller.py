import json
from datetime import datetime, timezone

from factory_capability_requirement_inference import (
    FactoryCapabilityRequirementInference
)

from factory_autonomous_activation_controller import (
    FactoryAutonomousActivationController
)


class FactoryAutonomousController:

    def __init__(self):

        self.requirements = (
            FactoryCapabilityRequirementInference()
        )

        self.activation = (
            FactoryAutonomousActivationController()
        )


    def evaluate_and_execute(self, objective):

        capability_report = (
            self.requirements.evaluate(objective)
        )

        decision = (
            capability_report["decision"]
        )


        if decision["action"] == "activate_existing_factory":

            activation = self.activation.activate(
                objective
            )

            return {
                "timestamp":
                    datetime.now(timezone.utc).isoformat(),

                "component":
                    "factory_autonomous_controller",

                "objective":
                    objective,

                "capability_evaluation":
                    capability_report,

                "action":
                    "activated_existing_factory",

                "activation":
                    activation
            }


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_autonomous_controller",

            "objective":
                objective,

            "capability_evaluation":
                capability_report,

            "action":
                "construction_required"
        }



def run():

    controller = FactoryAutonomousController()

    return controller.evaluate_and_execute(
        "autonomous factory lifecycle execution"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
