from typing import Any, Dict, List


class FactoryDecisionOptionAdapter:
    """
    Converts Factory planning output into Decision Intelligence options.
    """

    def __init__(self):
        self._history = []

    def build_options(
        self,
        plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        priority = plan.get("priority", 0)

        options = []

        for task in plan.get("tasks", []):
            options.append(
                {
                    "action": task,
                    "score": priority,
                    "context": plan.get("context"),
                    "validation": plan.get("validation", []),
                    "rollback": plan.get("rollback", []),
                }
            )

        self._history.append(
            {
                "plan": plan,
                "options": options,
            }
        )

        return options

    def history(self):
        return self._history
