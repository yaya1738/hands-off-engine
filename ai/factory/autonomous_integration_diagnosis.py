
from typing import Any, Dict


class FactoryAutonomousIntegrationDiagnosis:

    def __init__(self):
        self._history = []

    def diagnose(self, report: Dict[str, Any]) -> Dict[str, Any]:
        diagnosis = {
            "status": "INTEGRATION_DIAGNOSIS",
            "healthy": report.get("healthy", False),
            "failures": [],
        }

        for component, exists in report.get("components", {}).items():
            if not exists:
                diagnosis["failures"].append({
                    "component": component,
                    "issue": "missing_component",
                    "severity": "high",
                })

        if not diagnosis["healthy"] and not diagnosis["failures"]:
            diagnosis["failures"].append({
                "component": "unknown",
                "issue": "integration_failure",
                "severity": "medium",
            })

        self._history.append(diagnosis)

        return diagnosis

    def history(self):
        return self._history
