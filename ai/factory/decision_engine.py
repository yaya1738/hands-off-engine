from typing import Any, Dict, List


class FactoryDecisionEngine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        if state.get("health") == "DOWN":
            return "RECOVER"

        if state.get("success_rate", 1) <= 0.5:
            return "IMPROVE"

        recommendation = state.get(
            "recommendation"
        )

        if recommendation == "improve":
            return "OPTIMIZE"

        if recommendation == "continue":
            return "CONTINUE"

        return "CONTINUE"


    def decide(
        self,
        state: Dict[str, Any],
    ):
        decision = self.evaluate(
            state
        )

        result = {
            "confidence": state.get(
                "performance",
                0,
            ),
            "decision": decision,
            "reason": self.reason(
                decision
            ),
        }

        if not hasattr(self, "_history"):
            self._history = []

        self._history.append(
            result
        )

        return result


    def analyze(
        self,
        health,
        history,
        telemetry,
    ):
        return self.decide(
            {
                "recommendation": (
                    "improve"
                    if health.get("status") == "FAILED"
                    else "continue"
                ),
                "performance": (
                    0
                    if health.get("status") == "FAILED"
                    else 1
                ),
                "telemetry": telemetry,
            }
        )


    def history(self):
        return getattr(
            self,
            "_history",
            [],
        )


    def reason(
        self,
        decision: str,
    ):
        reasons = {
            "RECOVER": "runtime health failure",
            "IMPROVE": "performance below target",
            "CONTINUE": "system operating normally",
        }

        return reasons.get(
            decision,
            "unknown",
        )

    def history(self):
        return self._history
