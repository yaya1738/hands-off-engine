import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime
from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


class FactoryAuthorityGateway:

    def __init__(self):
        self.runtime = FactoryRuntime()
        self.orchestrator = FactoryDevelopmentOrchestrator()
        self.pipeline = FactoryDevelopmentPipeline()
        self.completion = FactoryCompletionWiringAdapter()


    def submit(self, objective):

        goal_result = self.runtime.submit_goal(
            objective
        )

        task = {
            "goal": objective,
            "type": "capability_build"
        }

        construction_result = self.pipeline.run_development_cycle(
            task
        )

        return {
            "goal": goal_result,
            "construction": construction_result,
            "status": "ready_for_review"
        }


def run():

    gateway = FactoryAuthorityGateway()

    result = gateway.submit(
        "authority gateway integration test"
    )

    return {
        "timestamp":
            datetime.now(timezone.utc).isoformat(),

        "component":
            "factory_authority_gateway",

        "result":
            result
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
