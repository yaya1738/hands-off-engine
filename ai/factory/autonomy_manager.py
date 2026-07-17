from datetime import datetime, timezone


class FactoryAutonomyManager:

    def __init__(self, runtime):
        self.runtime = runtime

    def evaluate(self, objective):

        components = (
            self.runtime.component_inventory()
        )

        capability_count = components.get(
            "component_count",
            0
        )

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "objective":
                objective,

            "factory_components":
                capability_count,

            "status":
                "ready" if capability_count > 0 else "blocked",
        }


    def execute(self, objective):

        evaluation = self.evaluate(
            objective
        )

        if evaluation["status"] != "ready":
            return {
                "evaluation": evaluation,
                "status": "blocked",
            }

        result = self.runtime.autonomous_execute(
            objective
        )

        return {
            "evaluation": evaluation,
            "execution": result,
        }
