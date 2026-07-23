from pathlib import Path
import subprocess
from typing import Any, Dict


class FactoryChangeValidation:
    def __init__(self):
        self._history = []

    def _run(self, command):
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    def validate_action_router_integration(self):
        runtime = Path(
            "ai/factory/runtime.py"
        )

        checks = {}

        if not runtime.exists():
            return {
                "status": "FAIL",
                "error": "runtime.py missing",
            }

        text = runtime.read_text()

        checks["router_import"] = (
            "FactoryActionRouter" in text
        )

        checks["router_initialized"] = (
            "self.action_router = FactoryActionRouter" in text
        )

        checks["improvement_gateway"] = (
            "trigger_improvement_pipeline" in text
        )

        test = self._run(
            """python3 - <<'PY'
from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

route = r.action_router.route({
    "decision": "IMPROVE",
    "capability_context": {}
})

result = r.execute(
    "factory validation test"
)

assert route["action"] == "improvement_pipeline"
assert result["success"] is True

print("VALIDATION_PASS")
PY"""
        )

        checks["runtime_execution"] = test["success"]

        status = (
            "PASS"
            if all(checks.values())
            else "FAIL"
        )

        report = {
            "status": status,
            "checks": checks,
        }

        self._history.append(report)

        return report

    def history(self):
        return self._history
