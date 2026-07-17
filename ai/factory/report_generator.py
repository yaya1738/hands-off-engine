from typing import Any, Dict, List


class FactoryReportGenerator:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def generate(
        self,
        integrity=None,
        operator=None,
        maintenance=None,
    ):
        healthy = bool(
            integrity
            and integrity.get("healthy")
        )

        ready = bool(
            maintenance
            and maintenance.get(
                "maintenance_ready",
                False,
            )
        )

        report = {
            "factory_health": (
                "healthy"
                if healthy
                else "attention_required"
            ),
            "maintenance_ready": ready,
            "operator": operator,
            "maintenance": maintenance,
            "next_step": (
                "continue_development"
                if healthy and ready
                else "inspect_system"
            ),
        }

        self._history.append(report)

        return report

    def history(self):
        return self._history
