from typing import Any, Dict, List


class FactoryDecisionEngine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        if state.get(
            "health"
        ) == "DOWN":
            return "RECOVER"

        if state.get(
            "success_rate",
            1,
        ) < 0.8:
            return "IMPROVE"

        return "CONTINUE"

    def decide(
        self,
        state: Dict[str, Any],
    ):
        decision = self.evaluate(
            state
        )

        result = {
            "decision": decision,
            "reason": self.reason(
                decision
            ),
        }

        self._history.append(
            result
        )

        return result

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
