import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence
from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


class FactoryAuthorityGateway:
    """Canonical external authority boundary for Factory operations.

    The gateway owns ingress; the supplied runtime owns execution/state.
    No gateway-created shadow runtime is used when an existing runtime is
    supplied by an autonomous caller.
    """

    def __init__(self, runtime=None):
        self.runtime = runtime or FactoryRuntime()
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
        """Plan/submit a goal only; never execute it."""
        if objective is None:
            raise ValueError("objective is required")
        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")

        return self.runtime.submit_goal(objective)

    def submit_development_request(self, objective, context=None):
        """External development-planning ingress; does not execute work."""
        if objective is None:
            raise ValueError("objective is required")
        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")
        return self.runtime.submit_development_request(objective, context or "")

    def execute(self, objective):
        """Canonical external execution ingress into the supplied runtime."""
        if objective is None:
            raise ValueError("objective is required")
        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")

        result = self.runtime.execute(objective)
        self.runtime.emit_event(
            "authority.execution_completed",
            {
                "objective": objective,
                "success": bool(result.get("success"))
                if isinstance(result, dict) else False,
            },
        )
        return result

    def complete_reviewed_goal(self, review_request, improvement, result, artifact):
        return self.completion.complete_reviewed_task(
            review_request, 0, improvement, result, artifact
        )

    def report(self):
        return {
            "component": "FactoryAuthorityGateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shared_state": True,
        }


if __name__ == "__main__":
    print(json.dumps(FactoryAuthorityGateway().report(), indent=2))
