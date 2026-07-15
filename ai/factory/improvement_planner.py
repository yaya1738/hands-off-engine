from typing import Any, Dict, List


class FactoryImprovementPlanner:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def plan(
        self,
        assessment: Dict[str, Any],
    ):
        gaps = assessment.get(
            "gaps",
            [],
        )

        tasks = [
            f"address {gap}"
            for gap in gaps
        ]

        result = {
            "goal": "improve factory performance",
            "tasks": tasks,
            "priority": self.prioritize(
                assessment
            ),
        }

        self._history.append(
            result
        )

        return result

    def prioritize(
        self,
        assessment: Dict[str, Any],
    ):
        health = assessment.get(
            "health",
            1,
        )

        return round(
            1 - health,
            2,
        )

    def history(self):
        return self._history
