from typing import Any, Dict, List


class FactoryExecutionHandoffAdapter:
    def __init__(self):
        self._handoffs: List[Dict[str, Any]] = []

    def create_handoff(
        self,
        routing_decision: Dict[str, Any],
    ):
        handoff = {
            "target": routing_decision.get("target"),
            "execution_requirements": routing_decision.get(
                "execution_requirements",
                [],
            ),
            "verification_requirements": routing_decision.get(
                "verification_requirements",
                [],
            ),
            "capability_context": routing_decision.get(
                "capability_context",
                {},
            ),
            "status": "HANDOFF_CREATED",
        }

        self._handoffs.append(handoff)

        return {
            "created": True,
            "handoff": handoff,
        }

    def validate_handoff(self, index: int = -1):
        if not self._handoffs:
            return {
                "valid": False,
                "reason": "NOT_FOUND",
            }

        handoff = self._handoffs[index]

        return {
            "valid": bool(
                handoff["status"]
                and handoff["execution_requirements"] is not None
                and handoff["verification_requirements"] is not None
            ),
            "handoff": handoff,
        }

    def history(self):
        return self._handoffs
