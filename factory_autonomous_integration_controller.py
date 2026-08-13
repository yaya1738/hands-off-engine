import json
from datetime import datetime, timezone

from ai.factory.authority_gateway import FactoryAuthorityGateway
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.artifact_registry import FactoryArtifactRegistry


class FactoryAutonomousIntegrationController:

    def __init__(self):
        self.gateway = FactoryAuthorityGateway()
        self.pipeline = FactoryDevelopmentPipeline()
        self.registry = FactoryArtifactRegistry()


    def discover_capabilities(self):

        return {
            "authority_gateway": hasattr(
                self.gateway,
                "submit_goal"
            ),

            "execution_ingress": hasattr(
                self.gateway,
                "execute"
            ),

            "construction_pipeline": hasattr(
                self.gateway,
                "pipeline"
            ),

            "completion_adapter": hasattr(
                self.gateway,
                "completion"
            ),

            "artifact_registry": hasattr(
                self.gateway,
                "registry"
            )
        }


    def decide(self, capabilities):

        required = [
            "authority_gateway",
            "execution_ingress",
            "construction_pipeline",
            "completion_adapter",
            "artifact_registry",
        ]

        missing = [
            item
            for item in required
            if not capabilities[item]
        ]

        if not missing:
            return {
                "decision": "reuse_existing_factory",
                "action": "activate_existing_lifecycle",
                "missing": []
            }

        return {
            "decision": "construction_required",
            "action": "request_factory_build",
            "missing": missing
        }


    def execute(self, goal):

        capabilities = self.discover_capabilities()

        decision = self.decide(
            capabilities
        )

        result = {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_autonomous_integration_controller",

            "goal":
                goal,

            "capabilities":
                capabilities,

            "decision":
                decision
        }


        if decision["decision"] == "construction_required":

            result["construction_request"] = (
                self.pipeline.run_development_cycle(
                    {
                        "goal": goal,
                        "type": "capability_build"
                    }
                )
            )

        else:

            # The authority gateway is the single supported execution
            # ingress. Autonomous activation must use it rather than
            # bypassing directly into submit_goal or runtime internals.
            result["activation"] = (
                self.gateway.execute(
                    goal
                )
            )


        return result



def run():

    controller = FactoryAutonomousIntegrationController()

    return controller.execute(
        "autonomous authority lifecycle execution"
    )


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2
        )
    )
