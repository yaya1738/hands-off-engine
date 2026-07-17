from typing import Any, Dict, List


class FactoryMaintenanceAgent:
    def __init__(
        self,
        operator=None,
    ):
        self.operator = operator
        self._history: List[Dict[str, Any]] = []

    def inspect(
        self,
        runtime,
    ):
        if self.operator:
            operator_status = self.operator.assess(runtime)
        else:
            operator_status = {
                "status": "unknown",
            }

        result = {
            "operator_status": operator_status,
            "maintenance_ready": (
                operator_status.get("status") == "healthy"
            ),
        }

        self._history.append(result)

        return result

    def recommend(
        self,
        inspection: Dict[str, Any],
    ):
        if inspection.get("maintenance_ready"):
            action = "continue_development"
        else:
            action = "repair_before_development"

        result = {
            "recommended_action": action,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
