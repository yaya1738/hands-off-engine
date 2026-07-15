from typing import Any, Dict, List


class FactoryImprovementPolicy:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        improvement: Dict[str, Any],
    ):
        risk = improvement.get(
            "risk",
            "unknown",
        )

        if risk == "high":
            decision = "BLOCK"

        elif risk == "medium":
            decision = "REVIEW"

        else:
            decision = "ALLOW"

        result = {
            "improvement": improvement,
            "decision": decision,
        }

        self._history.append(
            result
        )

        return result

    def allow(
        self,
        improvement,
    ):
        return self.evaluate(
            {
                **improvement,
                "risk": "low",
            }
        )

    def block(
        self,
        improvement,
    ):
        return self.evaluate(
            {
                **improvement,
                "risk": "high",
            }
        )

    def history(self):
        return self._history
