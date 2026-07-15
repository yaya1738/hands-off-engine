from typing import Any, Dict, List


class FactoryRiskManagement:
    def __init__(self):
        self.assessments: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def assess_risk(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "risk_assessed": True,
            "action": action,
            "risk": "LOW",
        }

        self.assessments.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def calculate_exposure(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "exposure_calculated": True,
            "exposure": 0,
        }

        self._history.append(
            result
        )

        return result

    def approve_action(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "approved": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def reject_action(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "rejected": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
