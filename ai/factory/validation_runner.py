from typing import Any, Dict, List
import subprocess


class FactoryValidationRunner:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def run_compile_check(
        self,
        target: str,
    ):
        result = self._run_command(
            [
                "python",
                "-m",
                "py_compile",
                target,
            ]
        )

        self.results.append(result)
        self._history.append(result)

        return result

    def run_test_check(
        self,
        target: str = "tests",
    ):
        result = self._run_command(
            [
                "pytest",
                target,
            ]
        )

        self.results.append(result)
        self._history.append(result)

        return result

    def validate_change(
        self,
        change: Dict[str, Any],
    ):
        result = {
            "change": change,
            "status": "validation_started",
        }

        self._history.append(result)

        return result

    def _run_command(
        self,
        command: List[str],
    ):
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            result = {
                "command": command,
                "success": process.returncode == 0,
                "output": process.stdout[-1000:],
                "error": process.stderr[-1000:],
            }

        except Exception as e:
            result = {
                "command": command,
                "success": False,
                "error": str(e),
            }

        return result

    def report(self):
        return {
            "results": self.results,
            "count": len(self.results),
        }

    def history(self):
        return self._history
