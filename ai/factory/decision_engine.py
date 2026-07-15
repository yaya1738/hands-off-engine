from typing import Any, Dict, List


class FactoryDecisionEngine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        context: Dict[str, Any],
    ):
        health = context.get(
            "health",
            "UNKNOWN",
        )

        risk = context.get(
            "risk",
            "UNKNOWN",
        )

        if health == "DEGRADED":
            decision = {
                "decision": "RECOVER",
                "reason": "health_degraded",
                "confidence": 0.8,
            }

        elif risk == "HIGH":
            decision = {
                "decision": "ESCALATE",
                "reason": "high_risk",
                "confidence": 0.7,
            }

        else:
            decision = {
                "decision": "CONTINUE",
                "reason": "stable",
                "confidence": 0.9,
            }

        self._history.append(
            decision
        )

        return decision

    def decide(
        self,
        context,
    ):
        return self.evaluate(
            context
        )

    def history(self):
        return self._history
