import json
from datetime import datetime, timezone

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryAutonomousCapabilityRouter:

    def __init__(self):
        self.gateway = FactoryAuthorityGateway()


    def inspect(self):

        capabilities = {
            "authority_gateway":
                hasattr(self.gateway, "submit_goal"),

            "completion":
                hasattr(self.gateway, "complete_reviewed_goal"),

            "reporting":
                hasattr(self.gateway, "report"),
        }

        missing = [
            key
            for key, value in capabilities.items()
            if not value
        ]

        return capabilities, missing


    def route(self, objective):

        capabilities, missing = self.inspect()


        if missing:

            return {
                "timestamp":
                    datetime.now(timezone.utc).isoformat(),

                "decision":
                    "capability_build_required",

                "missing":
                    missing,

                "action":
                    "route_to_factory_builder"
            }


        lifecycle = self.gateway.submit_goal(
            objective
        )

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "decision":
                "reuse_existing_factory",

            "capabilities":
                capabilities,

            "action":
                "activate_lifecycle",

            "lifecycle":
                lifecycle,
        }



def run():

    router = FactoryAutonomousCapabilityRouter()

    return router.route(
        "autonomous capability routing verification"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
