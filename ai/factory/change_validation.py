from pathlib import Path
from typing import Any, Dict


class FactoryChangeValidation:
    """Read-only structural validation; execution belongs to FactoryAuthorityGateway/CI."""

    def __init__(self):
        self._history = []

    def _run(self, command):
        result = {
            "success": False,
            "stdout": "",
            "stderr": "[FACTORY-AUTHORITY] legacy validation execution is disabled; submit through FactoryAuthorityGateway",
            "command": command,
        }
        self._history.append(result)
        return result

    def validate_action_router_integration(self):
        runtime = Path("ai/factory/runtime.py")
        checks = {}
        if not runtime.exists():
            return {"status": "FAIL", "error": "runtime.py missing"}

        text = runtime.read_text()
        checks["router_import"] = "FactoryActionRouter" in text
        checks["router_initialized"] = "self.action_router = FactoryActionRouter" in text
        checks["improvement_gateway"] = "trigger_improvement_pipeline" in text
        checks["runtime_execution"] = False

        report = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
            "action": "submit_validation_request",
            "next_step": "FactoryAuthorityGateway",
        }
        self._history.append(report)
        return report

    def history(self):
        return self._history
