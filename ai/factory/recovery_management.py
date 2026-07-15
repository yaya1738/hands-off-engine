from typing import Any, Dict, List


class FactoryRecoveryManagement:
    def __init__(self):
        self.incidents: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def detect_failure(
        self,
        failure: Dict[str, Any],
    ):
        result = {
            "detected": True,
            "failure": failure,
        }

        self._history.append(result)

        return result

    def attempt_recovery(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "attempted": True,
            "action": action,
        }

        self._history.append(result)

        return result

    def validate_recovery(
        self,
        recovery: Dict[str, Any],
    ):
        result = {
            "validated": True,
            "recovery": recovery,
        }

        self._history.append(result)

        return result

    def record_incident(
        self,
        incident: Dict[str, Any],
    ):
        self.incidents.append(
            incident
        )

        result = {
            "recorded": True,
            "incident": incident,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
