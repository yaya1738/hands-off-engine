import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime
from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryAutonomousDiscoveryRouter:

    def __init__(self):
        self.runtime = FactoryRuntime()
        self.gateway = FactoryAuthorityGateway()


    def discover(self):

        inventory = self.runtime.component_inventory()

        return inventory.get(
            "components",
            []
        )


    def evaluate(self, objective):

        components = self.discover()

        required = [
            "goal_management",
            "development_pipeline",
            "development_tracker",
        ]

        missing = [
            item
            for item in required
            if item not in components
        ]


        if missing:
            return {
                "timestamp":
                    datetime.now(timezone.utc).isoformat(),

                "decision":
                    "missing_capabilities",

                "missing":
                    missing,

                "action":
                    "route_to_factory_construction"
            }


        lifecycle = self.gateway.submit_goal(
            objective
        )


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "decision":
                "reuse_existing_factory",

            "action":
                "activate_existing_lifecycle",

            "discovered_components":
                components,

            "lifecycle":
                lifecycle
        }



def run():

    router = FactoryAutonomousDiscoveryRouter()

    return router.evaluate(
        "autonomous discovery routing verification"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
