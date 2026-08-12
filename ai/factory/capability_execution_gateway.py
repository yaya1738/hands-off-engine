from datetime import datetime, timezone
from typing import Any, Dict


class FactoryCapabilityExecutionGateway:
    """
    Bounded external-agent execution seam.

    External agents submit data-only capability requests. They do not receive
    direct access to Factory components or callables. The gateway owns the
    routing -> handoff -> execution -> verification -> audit -> learning path.
    """

    ALLOWED_FIELDS = {
        "capability",
        "action",
        "intent",
        "parameters",
        "context",
    }

    def __init__(self, runtime):
        self.runtime = runtime

    def submit(self, request: Dict[str, Any]):
        if not isinstance(request, dict):
            raise ValueError("capability request must be an object")

        unknown = set(request) - self.ALLOWED_FIELDS
        if unknown:
            raise ValueError(
                "capability request contains unsupported fields: "
                + ", ".join(sorted(unknown))
            )

        capability = str(request.get("capability", "")).strip()
        action = str(request.get("action", "")).strip()

        if not capability:
            raise ValueError("capability is required")
        if not action:
            raise ValueError("action is required")

        parameters = request.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be an object")

        decision = {
            "decision": action,
            "capability_context": {
                "capability": capability,
                "intent": request.get("intent", ""),
                "context": request.get("context", ""),
                "parameters": parameters,
            },
        }

        audit = getattr(self.runtime, "action_audit", None)
        if audit:
            audit.record_decision(decision)

        routed = self.runtime.action_router.route(decision)
        if audit:
            audit.record_action(routed)

        handoff = self.runtime.execution_handoff.create_handoff(
            {
                "target": routed.get("action"),
                "execution_requirements": ["factory_action_router"],
                "verification_requirements": [
                    "handoff_validation",
                    "runtime_integrity",
                ],
                "capability_context": decision["capability_context"],
            }
        )

        validation = self.runtime.execution_handoff.validate_handoff()
        if not validation.get("valid"):
            outcome = {
                "success": False,
                "status": "HANDOFF_REJECTED",
                "validation": validation,
            }
            if audit:
                audit.record_outcome(outcome)
            return outcome

        execution_id = (
            "capability-"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        )
        self.runtime.execution.create_execution(
            execution_id,
            {
                "capability": capability,
                "action": action,
                "parameters": parameters,
            },
        )
        self.runtime.execution.start_execution(execution_id)

        execution_result = self.runtime.action_router.execute(routed)

        self.runtime.execution.complete_execution(execution_id)
        tracked = self.runtime.execution.track_execution(execution_id)

        verification = self.runtime.integrity_checker.check_runtime(
            self.runtime
        )

        outcome = {
            "success": verification.get("healthy", False),
            "status": "COMPLETED" if verification.get("healthy") else "VERIFICATION_FAILED",
            "capability": capability,
            "action": action,
            "handoff": handoff,
            "validation": validation,
            "execution": execution_result,
            "tracked_execution": tracked,
            "verification": verification,
        }

        if audit:
            audit.record_outcome(outcome)

        self.runtime.learning.record_experience(
            {
                "type": "factory_capability_execution",
                "capability": capability,
                "action": action,
                "outcome": outcome,
            }
        )
        self.runtime.learning.analyze_outcome(outcome)

        return outcome
