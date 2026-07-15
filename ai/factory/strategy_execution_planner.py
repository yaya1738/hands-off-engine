from typing import Any, Dict, List


class FactoryStrategyExecutionPlanner:
    def __init__(self):
        self.plans: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_plan(
        self,
        strategy: Dict[str, Any],
    ):
        result = {
            "plan_created": True,
            "strategy": strategy,
        }

        self.plans.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def decompose(
        self,
        plan: Dict[str, Any],
    ):
        result = {
            "tasks": [
                plan
            ],
        }

        self._history.append(
            result
        )

        return result

    def prioritize_tasks(
        self,
        tasks: List[Dict[str, Any]],
    ):
        result = {
            "priority_task": (
                tasks[0]
                if tasks
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def validate_plan(
        self,
        plan: Dict[str, Any],
    ):
        result = {
            "valid": True,
            "plan": plan,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
