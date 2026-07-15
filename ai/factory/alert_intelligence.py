from typing import Any, Dict, List


class FactoryAlertIntelligence:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_alert(
        self,
        alert: Dict[str, Any],
    ):
        self.alerts.append(alert)

        result = {
            "created": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def evaluate_alert(
        self,
        alert: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def escalate_alert(
        self,
        alert: Dict[str, Any],
    ):
        result = {
            "escalated": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def resolve_alert(
        self,
        alert: Dict[str, Any],
    ):
        result = {
            "resolved": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
