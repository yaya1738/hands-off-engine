import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime


class FactoryCapabilityRequirementInference:

    def __init__(self):
        self.runtime = FactoryRuntime()


    def discover_components(self):

        inventory = self.runtime.component_inventory()

        return set(
            inventory.get("components", [])
        )


    def infer_requirements(self, objective):

        # Lifecycle capability map
        lifecycle_requirements = {
            "goal_intake": "goal_management",
            "planning": "planning",
            "construction": "development_pipeline",
            "tracking": "development_tracker",
            "execution": "execution",
            "validation": "integrity_checker",
            "learning": "learning_loop",
            "optimization": "optimization",
            "reporting": "report_generator",
        }

        return lifecycle_requirements


    def evaluate(self, objective):

        available = self.discover_components()

        requirements = self.infer_requirements(
            objective
        )

        missing = []

        available_map = {}

        for capability, component in requirements.items():

            available_map[capability] = (
                component in available
            )

            if component not in available:
                missing.append(
                    {
                        "capability": capability,
                        "component": component
                    }
                )


        if missing:

            decision = {
                "status": "MISSING_CAPABILITIES",
                "action": "route_to_construction",
                "missing": missing
            }

        else:

            decision = {
                "status": "CAPABILITIES_AVAILABLE",
                "action": "activate_existing_factory"
            }


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_capability_requirement_inference",

            "objective":
                objective,

            "available_components":
                list(available),

            "capability_map":
                available_map,

            "decision":
                decision
        }



def run():

    resolver = FactoryCapabilityRequirementInference()

    return resolver.evaluate(
        "autonomous lifecycle execution"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
