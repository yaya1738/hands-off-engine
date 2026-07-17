from typing import Any, Dict, List


class FactoryChangeImpactAnalyzer:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ):
        before_health = before.get(
            "factory_health"
        )

        after_health = after.get(
            "factory_health"
        )

        result = {
            "before_health": before_health,
            "after_health": after_health,
            "impact": (
                "positive"
                if before_health != "healthy"
                and after_health == "healthy"
                else "neutral"
                if before_health == after_health
                else "negative"
            ),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
