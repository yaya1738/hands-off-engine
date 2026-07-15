from typing import Any, Dict, List


class FactoryGoalManagement:
    def __init__(self):
        self.goals: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_goal(
        self,
        goal: Dict[str, Any],
    ):
        self.goals.append(
            goal
        )

        result = {
            "created": True,
            "goal": goal,
        }

        self._history.append(
            result
        )

        return result

    def prioritize_goals(self):
        result = {
            "priority_goal": (
                self.goals[0]
                if self.goals
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def track_progress(
        self,
        goal: Dict[str, Any],
        progress: Any,
    ):
        result = {
            "tracked": True,
            "goal": goal,
            "progress": progress,
        }

        self._history.append(
            result
        )

        return result

    def complete_goal(
        self,
        goal: Dict[str, Any],
    ):
        result = {
            "completed": True,
            "goal": goal,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
