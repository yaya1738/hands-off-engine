import json
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.artifact_registry import FactoryArtifactRegistry


class FactoryConstructionRouter:

    def __init__(self):
        self.orchestrator = FactoryDevelopmentOrchestrator()
        self.pipeline = FactoryDevelopmentPipeline()
        self.registry = FactoryArtifactRegistry()


    def find_existing(self, goal):
        artifacts = self.registry.list_artifacts()

        for artifact in artifacts:
            text = json.dumps(artifact).lower()
            if goal.lower() in text:
                return artifact

        return None


    def construct(self, goal):

        existing = self.find_existing(goal)

        if existing:
            return {
                "decision": "reuse_existing_artifact",
                "artifact": existing
            }


        task = {
            "goal": goal,
            "type": "capability_build",
            "requested_at": datetime.now(timezone.utc).isoformat()
        }

        created_task = self.orchestrator.create_development_task(task)

        result = self.pipeline.run_development_cycle(
            created_task
        )

        return {
            "decision": "new_construction_pipeline",
            "task": created_task,
            "result": result
        }


def run(goal):
    router = FactoryConstructionRouter()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_router",
        "goal": goal,
        "result": router.construct(goal)
    }


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
