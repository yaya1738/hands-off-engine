from typing import Any, Dict, List


class FactoryGoalManager:
    def __init__(self):
        self.goals: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_goal(
        self,
        name: str,
        goal: Dict[str, Any],
    ):
        self.goals[name] = goal

        result = {
            "registered": True,
            "goal": name,
        }

        self._history.append(result)

        return result

    def prioritize_goals(self):
        result = {
            "prioritized": True,
            "count": len(self.goals),
        }

        self._history.append(result)

        return result

    def evaluate_progress(
        self,
        name: str,
        progress: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "goal": name,
            "progress": progress,
        }

        self._history.append(result)

        return result

    def complete_goal(
        self,
        name: str,
    ):
        result = {
            "completed": True,
            "goal": name,
        }

        self._history.append(result)

        return result

    def revise_goal(
        self,
        name: str,
        revision: Dict[str, Any],
    ):
        result = {
            "revised": True,
            "goal": name,
            "revision": revision,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
