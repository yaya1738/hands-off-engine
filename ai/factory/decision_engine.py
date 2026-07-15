from typing import Any, Dict, List


class FactoryDecisionEngine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def decide(
        self,
        feedback: Dict[str, Any],
    ) -> Dict[str, Any]:

        recommendation = feedback.get(
            "recommendation",
            "review",
        )

        performance = feedback.get(
            "performance",
            0,
        )

        if recommendation == "continue":
            decision = "CONTINUE"

        elif recommendation == "improve":
            decision = "OPTIMIZE"

        else:
            decision = "REVIEW"

        result = {
            "decision": decision,
            "confidence": performance,
            "reason": feedback.get(
                "trend",
                "unknown",
            ),
        }

        self._history.append(result)

        return result

    def evaluate(
        self,
        feedback: Dict[str, Any],
    ):
        return self.decide(feedback)

    def history(self):
        return self._history
