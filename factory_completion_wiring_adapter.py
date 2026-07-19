import json
from datetime import datetime, timezone

from ai.factory.runtime import (
    FactoryDevelopmentTracker,
    FactoryImprovementApproval,
    FactoryImprovementQueue,
)

from ai.factory.artifact_registry import (
    FactoryArtifactRegistry,
)


class FactoryCompletionWiringAdapter:

    def __init__(
        self,
        tracker=None,
        registry=None,
        approval=None,
        queue=None,
    ):
        self.approval = approval or FactoryImprovementApproval()
        self.tracker = tracker or FactoryDevelopmentTracker()
        self.queue = queue or FactoryImprovementQueue()
        self.registry = registry or FactoryArtifactRegistry()


    def complete_reviewed_task(
        self,
        request,
        task_index,
        improvement,
        result,
        artifact
    ):

        approval_result = self.approval.approve(
            request
        )

        completion_result = self.tracker.complete_task(
            task_index
        )

        queue_result = self.queue.complete(
            improvement,
            result
        )

        self.registry.register_artifact(
            artifact["artifact_id"],
            artifact["task_id"],
            artifact["artifact_type"],
            artifact["location"]
        )

        return {
            "approval": approval_result,
            "task_completion": completion_result,
            "queue_completion": queue_result,
            "artifact_registered": True
        }


def run():

    adapter = FactoryCompletionWiringAdapter()

    return {
        "timestamp":
            datetime.now(timezone.utc).isoformat(),

        "component":
            "factory_completion_wiring_adapter",

        "status":
            "adapter_created",

        "available_methods":
            [
                "complete_reviewed_task"
            ]
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
