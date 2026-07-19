import json
from datetime import datetime, timezone

from factory_autonomous_controller import (
    FactoryAutonomousController
)


class FactoryAutonomousDecisionReporter:

    def __init__(self):

        self.controller = (
            FactoryAutonomousController()
        )


    def summarize(self, objective):

        result = self.controller.evaluate_and_execute(
            objective
        )

        capability = result.get(
            "capability_evaluation",
            {}
        )

        capability_map = capability.get(
            "capability_map",
            {}
        )

        available = sum(
            1 for value in capability_map.values()
            if value is True
        )

        missing = sum(
            1 for value in capability_map.values()
            if value is False
        )


        activation = result.get(
            "activation",
            {}
        )

        decision = (
            activation
            .get("decision", {})
            .get("classification", "unknown")
        )


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_autonomous_decision_reporter",

            "objective":
                objective,

            "decision":
                decision,

            "capabilities": {
                "available": available,
                "missing": missing
            },

            "action":
                result.get(
                    "action",
                    "unknown"
                ),

            "status":
                "READY"
        }



def run():

    reporter = FactoryAutonomousDecisionReporter()

    return reporter.summarize(
        "autonomous factory lifecycle execution"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
