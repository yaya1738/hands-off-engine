from typing import Any, Dict, List


class FactoryValidationRunner:
    """Read-only validation facade; execution belongs to FactoryAuthorityGateway/CI."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def run_compile_check(self, target: str):
        return self._disabled(["python", "-m", "py_compile", target])

    def run_test_check(self, target: str = "tests"):
        return self._disabled(["pytest", target])

    def validate_change(self, change: Dict[str, Any]):
        result = {
            "change": change,
            "status": "validation_requires_authority",
            "action": "submit_validation_request",
            "next_step": "FactoryAuthorityGateway",
        }
        self._history.append(result)
        return result

    def _disabled(self, command):
        result = {
            "command": command,
            "success": False,
            "error": "[FACTORY-AUTHORITY] legacy validation execution is disabled; submit through FactoryAuthorityGateway",
        }
        self.results.append(result)
        self._history.append(result)
        return result

    def report(self):
        return {"results": self.results, "count": len(self.results)}

    def history(self):
        return self._history
