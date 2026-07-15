from typing import Any, Dict, List


class FactoryAlertingNotification:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.notifications: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_alert(
        self,
        alert: Dict[str, Any],
    ):
        self.alerts.append(
            alert
        )

        result = {
            "created": True,
            "alert": alert,
        }

        self._history.append(result)

        return result

    def evaluate_condition(
        self,
        condition: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "triggered": False,
            "condition": condition,
        }

        self._history.append(result)

        return result

    def send_notification(
        self,
        notification: Dict[str, Any],
    ):
        self.notifications.append(
            notification
        )

        result = {
            "sent": True,
            "notification": notification,
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
