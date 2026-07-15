from typing import Any, Dict


class FactoryDashboard:
    def snapshot(
        self,
        health: Dict[str, Any],
        registry: Any,
        telemetry: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "health": health,
            "components": registry,
            "telemetry": telemetry,
            "state": state,
        }
