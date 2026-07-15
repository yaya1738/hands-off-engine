from typing import Any, Dict


class FactoryDecisionEngine:
    def analyze(
        self,
        health: Dict[str, Any],
        history: list,
        telemetry: Dict[str, Any],
    ) -> Dict[str, Any]:

        if health.get("status") != "HEALTHY":
            return {
                "action": "investigate",
                "reason": "factory_unhealthy",
            }

        failed = telemetry.get(
            "failed",
            0,
        )

        if failed > 0:
            return {
                "action": "review_failures",
                "reason": "failed_executions_detected",
            }

        return {
            "action": "continue",
            "reason": "factory_operating_normally",
        }
