from typing import Any, Dict


class FactoryLifecycleTrace:
    """
    Read-only lifecycle correlation layer.

    Does not execute, approve, or mutate Factory state.
    Reconstructs lifecycle state from existing Factory organs.
    """

    def __init__(self, runtime):
        self.runtime = runtime

    def trace(self) -> Dict[str, Any]:
        goal_history = self.runtime.goal_management.history()
        tracker_history = self.runtime.development_tracker.history()
        approval_history = self.runtime.improvement_approval.history()
        audit_history = self.runtime.improvement_audit.history()

        goal = goal_history[-1] if goal_history else {}
        task = tracker_history[-1] if tracker_history else {}
        approval = approval_history[-1] if approval_history else {}
        audit = audit_history[-1] if audit_history else {}

        artifact_id = None

        development_history = (
            self.runtime.development_pipeline.report()
            .get("history", [])
        )

        if development_history:
            latest_development = development_history[-1]

            artifact = latest_development.get(
                "artifact",
                {}
            )

            if isinstance(artifact, dict):
                artifact_id = artifact.get(
                    "artifact_id"
                )

        improvement = approval.get(
            "improvement",
            {}
        )

        return {
            "lifecycle_status": (
                "reconstructed"
                if goal and task and approval and audit
                else "incomplete"
            ),
            "goal": goal,
            "task_id": task.get("id"),
            "artifact_id": artifact_id,
            "approval_status": approval.get("status"),
            "improvement_id": (
                improvement.get("id")
                if isinstance(improvement, dict)
                else None
            ),
            "audit_present": bool(audit),
        }
