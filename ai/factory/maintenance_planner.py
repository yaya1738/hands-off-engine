from typing import Any, Dict, List


class FactoryMaintenancePlanner:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze_health(
        self,
        health: Dict[str, Any],
    ):
        issues = health.get(
            "issues",
            [],
        )

        if issues:
            return "MAINTENANCE_REQUIRED"

        return "HEALTHY"

    def plan(
        self,
        health: Dict[str, Any],
    ):
        status = self.analyze_health(
            health
        )

        if status == "MAINTENANCE_REQUIRED":
            plan = {
                "action": "RUN_CHECK",
                "priority": "HIGH",
                "components": health.get(
                    "issues",
                    [],
                ),
            }

        else:
            plan = {
                "action": "CONTINUE_MONITORING",
                "priority": "LOW",
                "components": [],
            }

        self._history.append(plan)

        return plan

    def history(self):
        return self._history
