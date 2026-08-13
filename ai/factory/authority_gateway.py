import json
import uuid
from datetime import datetime, timezone

from ai.factory.runtime import (
    FactoryRuntime,
    FactoryDevelopmentTracker,
    FactoryImprovementApproval,
    FactoryImprovementQueue,
)

from ai.factory.artifact_registry import FactoryArtifactRegistry
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence
from ai.factory.execution_journal import FactoryExecutionJournal

from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


class FactoryAuthorityGateway:

    def __init__(self, runtime=None, execution_journal=None):
        self.runtime = runtime or FactoryRuntime()
        self.execution_journal = execution_journal or FactoryExecutionJournal()

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

    def execute_autonomous(self, objective):
        """Authority-owned autonomous ingress preserving runtime readiness gates."""
        if objective is None:
            raise ValueError("objective is required")

        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")

        execution_id = str(uuid.uuid4())
        intent = {"objective": objective, "entrypoint": "FactoryAuthorityGateway"}
        self.execution_journal.record(execution_id, "STARTED", intent)

        try:
            result = self.runtime.autonomous_execute(objective)
            if isinstance(result, dict) and result.get("blocked"):
                self.execution_journal.record(
                    execution_id,
                    "CANCELLED",
                    {**intent, "result": result},
                )
            else:
                self.execution_journal.record(
                    execution_id,
                    "COMPLETED",
                    {**intent, "result": result},
                )
            return result
        except Exception as exc:
            self.execution_journal.record(
                execution_id,
                "FAILED",
                {**intent, "error": str(exc)},
            )
            raise

    def submit_goal(self, objective):
        capability_graph = FactoryCapabilityGraphIntelligence(
            self.runtime
        ).analyze()

        development_request = self.submit_development_request(
            objective,
            "authority_gateway_submission",
        )

        return {
            "development_request": development_request,
            "capability_graph": capability_graph,
            "state": "ready_for_review"
        }

    def submit_development_request(self, objective, context=None):
        """External development-ingress authority."""
        if objective is None:
            raise ValueError("objective is required")

        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")

        return self.runtime.submit_development_request(
            objective,
            context or "",
        )

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
