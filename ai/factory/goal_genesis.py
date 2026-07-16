from typing import Any, Dict, List


class FactoryGoalGenesis:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def generate_goal(
        self,
        recommendation: Dict[str, Any],
    ):
        goal = {
            "objective": recommendation.get(
                "objective",
                "Improve runtime performance",
            ),
            "priority": 2,
            "source": "self_improvement",
            "status": "candidate",
        }

        self._history.append(goal)

        return goal

    def history(self):
        return self._history
