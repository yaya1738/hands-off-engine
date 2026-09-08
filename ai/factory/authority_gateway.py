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
from ai.factory.execution_reconciler import FactoryExecutionReconciler
from ai.factory.restart_reconciliation import FactoryRestartReconciliation
from ai.decision.action_kernel import ActionDecision
from ai.decision.convergence import ConvergenceController
from factory_capability_requirement_inference import FactoryCapabilityRequirementInference
from factory_completion_wiring_adapter import FactoryCompletionWiringAdapter


class FactoryAuthorityGateway:
    def __init__(self, runtime=None, execution_journal=None):
        self.runtime = runtime or FactoryRuntime()
        self.execution_journal = execution_journal or FactoryExecutionJournal()
        self.restart_reconciliation = FactoryRestartReconciliation(
            FactoryExecutionReconciler(self.execution_journal)
        )
        self.startup_reconciliation = self.restart_reconciliation.on_startup()
        self.convergence = ConvergenceController()
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

    def decide_action(self, *, action, confidence, risk_score, costs, evidence,
                      max_risk=1.0, min_confidence=0.4, risk_check=None):
        # Keep the authority decision boundary self-contained even when a
        # controlled test or recovery path reconstructs this gateway without
        # calling __init__.
        if not hasattr(self, "convergence"):
            self.convergence = ConvergenceController()
        return self.convergence.evaluate(
            action=action, confidence=confidence, risk_score=risk_score,
            costs=costs, evidence=evidence, max_risk=max_risk,
            min_confidence=min_confidence, risk_check=risk_check,
        )

    @staticmethod
    def _verify_runtime_result(result, decision: ActionDecision) -> bool:
        return isinstance(result, dict) and result.get("success") is True

    def execute_autonomous(self, objective):
        """Route autonomous work through the canonical convergence lifecycle."""
        if objective is None:
            raise ValueError("objective is required")
        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")

        execution_id = str(uuid.uuid4())
        intent = {"objective": objective, "entrypoint": "FactoryAuthorityGateway"}
        self.execution_journal.record(execution_id, "STARTED", intent)
        try:
            capability_evaluation = FactoryCapabilityRequirementInference().evaluate(objective)
            capability_decision = capability_evaluation.get("decision", {})
            ready = capability_decision.get("action") == "activate_existing_factory"
            autonomy_report = self.runtime.report_autonomy_state(objective, capability_decision)

            if not ready:
                result = {"status": "blocked", "decision": capability_decision,
                          "autonomy_report": autonomy_report}
                self.execution_journal.record(execution_id, "CANCELLED", {**intent, "result": result})
                return result

            decision = self.decide_action(
                action=objective,
                confidence=1.0,
                risk_score=0.0,
                costs={"external_mutation": 0.0},
                evidence={
                    "capability_evaluation": capability_evaluation,
                    "capability_decision": capability_decision,
                    "autonomy_report": autonomy_report,
                },
                max_risk=0.0,
                min_confidence=1.0,
            )
            convergence = self.convergence.execute(
                decision=decision,
                executor=lambda approved: self.runtime.execute(objective),
                verifier=self._verify_runtime_result,
            )
            status = convergence.get("status")
            journal_state = "COMPLETED" if status == "verified" else "CANCELLED" if status == "blocked" else "FAILED"
            self.execution_journal.record(execution_id, journal_state, {**intent, "result": convergence})
            return {
                "status": status,
                "decision": decision.as_dict(),
                "execution": convergence.get("result"),
                "verified": convergence.get("verified", False),
                "convergence": convergence,
                "autonomy_report": autonomy_report,
            }
        except Exception as exc:
            self.execution_journal.record(execution_id, "FAILED", {**intent, "error": str(exc)})
            raise

    def submit_goal(self, objective):
        capability_graph = FactoryCapabilityGraphIntelligence(self.runtime).analyze()
        development_request = self.submit_development_request(objective, "authority_gateway_submission")
        return {"development_request": development_request, "capability_graph": capability_graph, "state": "ready_for_review"}

    def submit_development_request(self, objective, context=None):
        if objective is None:
            raise ValueError("objective is required")
        objective = str(objective).strip()
        if not objective:
            raise ValueError("objective must not be empty")
        return self.runtime.submit_development_request(objective, context or "")

    def approve_improvement(self, request):
        return self.approval.approve(request)

    def reject_improvement(self, request):
        return self.approval.reject(request)

    def validate_approved_improvement(self, request):
        return self.approval.validate_approved_request(request)

    def complete_reviewed_goal(self, review_request, improvement, result, artifact):
        return self.completion.complete_reviewed_task(review_request, 0, improvement, result, artifact)

    def report(self):
        return {
            "component": "FactoryAuthorityGateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shared_state": True,
            "startup_reconciliation": self.startup_reconciliation,
            "decision_kernel": "ai.decision.action_kernel",
            "convergence_controller": "ai.decision.convergence.ConvergenceController",
        }


if __name__ == "__main__":
    print(json.dumps(FactoryAuthorityGateway().report(), indent=2))
