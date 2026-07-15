from typing import Any, Dict, List


class FactoryGoalOptimizer:
    def __init__(
        self,
        mission=None,
    ):
        self.mission = mission
        self._history: List[Dict[str, Any]] = []

    def score_goals(self):
        if self.mission:
            goals = self.mission.goals

        else:
            goals = []

        result = {
            "scores": [
                {
                    "goal": goal,
                    "score": 1,
                }
                for goal in goals
            ],
        }

        self._history.append(
            result
        )

        return result

    def optimize(self):
        result = self.score_goals()

        output = {
            "optimized": True,
            "scores": result,
        }

        self._history.append(
            output
        )

        return output

    def adjust(
        self,
        goal: Dict[str, Any],
    ):
        result = {
            "adjusted": True,
            "goal": goal,
        }

        self._history.append(
            result
        )

        return result

    def select_best(self):
        scores = self.score_goals()

        best = (
            scores["scores"][0]
            if scores["scores"]
            else None
        )

        result = {
            "best": best,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
