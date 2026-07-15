from typing import Any, Dict, List


class FactoryMissionController:
    def __init__(self):
        self.goals: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def set_goal(
        self,
        goal: Dict[str, Any],
    ):
        self.goals.append(
            goal
        )

        result = {
            "goal_set": True,
            "goal": goal,
        }

        self._history.append(
            result
        )

        return result

    def evaluate_progress(self):
        result = {
            "goals": len(
                self.goals
            ),
            "progress": (
                "TRACKING"
                if self.goals
                else "NO_GOALS"
            ),
        }

        self._history.append(
            result
        )

        return result

    def prioritize(self):
        result = {
            "priority": (
                self.goals[0]
                if self.goals
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def advance(self):
        result = {
            "advanced": True,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
