from pathlib import Path
import subprocess
from typing import Any, Dict


class FactoryChangeValidation:
    def __init__(self):
        self._history = []

    def _run(self, command):
        """Run a fixed executable/argument vector without shell interpretation."""
        result = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    def validate_action_router_integration(self):
        runtime = Path("ai/factory/runtime.py")

        checks = {}

        if not runtime.exists():
            return {"status": "FAIL", "error": "runtime.py missing"}

        text = runtime.read_text()
        checks["router_import"] = "FactoryActionRouter" in text
        checks["router_initialized"] = "self.action_router = FactoryActionRouter" in text
        checks["improvement_gateway"] = "trigger_improvement_pipeline" in text

        validation_script = (
            "from ai.factory.runtime import FactoryRuntime\n\n"
            "r = FactoryRuntime()\n\n"
            "route = r.action_router.route({\n"
            '    "decision": "IMPROVE",\n'
            '    "capability_context": {}\n'
            "})\n\n"
            'result = r.execute("factory validation test")\n\n'
            'assert route["action"] == "improvement_pipeline"\n'
            'assert result["success"] is True\n\n'
            'print("VALIDATION_PASS")\n'
        )
        test = self._run(["python3", "-c", validation_script])
        checks["runtime_execution"] = test["success"]

        report = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
        }
        self._history.append(report)
        return report

    def history(self):
        return self._history
