import json
from datetime import datetime, timezone

from ai.factory.runtime import (
    FactoryRuntime,
    FactoryDevelopmentTracker,
    FactoryImprovementApproval,
    FactoryImprovementQueue,
)

from ai.factory.artifact_registry import FactoryArtifactRegistry
from ai.factory.development_pipeline import FactoryDevelopmentPipeline

from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


class FactoryAuthorityGateway:

    def __init__(self):

        self.runtime = FactoryRuntime()

        self.tracker = self.runtime.development_tracker
        self.approval = self.runtime.improvement_approval
        self.queue = self.runtime.improvement_queue
        self.registry = self.runtime.artifact_registry

        self.pipeline = self.runtime.development_pipeline

        self.completion = FactoryCompletionWiringAdapter(
            tracker=self.tracker,
            registry=self.registry,
            approval=self.approval,
            queue=self.queue,
        )


    def submit_goal(self, objective):

        development_request = self.runtime.submit_development_request(
            objective,
            "authority_gateway_submission",
        )

        return {
            "development_request": development_request,
            "state": "ready_for_review"
        }


    def complete_reviewed_goal(
        self,
        review_request,
        improvement,
        result,
        artifact
    ):

        return self.completion.complete_reviewed_task(
            review_request,
            0,
            improvement,
            result,
            artifact
        )


    def report(self):

        return {
            "component": "FactoryAuthorityGateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shared_state": True
        }


if __name__ == "__main__":
    print(json.dumps(
        FactoryAuthorityGateway().report(),
        indent=2
    ))
