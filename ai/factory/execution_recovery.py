from typing import Any, Dict, List


class FactoryExecutionRecovery:
    def __init__(self):
        self.failures: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def detect_failure(
        self,
        execution: Dict[str, Any],
    ):
        failed = (
            execution.get("status")
            == "FAILED"
        )

        result = {
            "failure_detected": failed,
            "execution": execution,
        }

        if failed:
            self.failures.append(
                execution
            )

        self._history.append(
            result
        )

        return result

    def retry(
        self,
        execution: Dict[str, Any],
    ):
        result = {
            "retried": True,
            "execution": execution,
        }

        self._history.append(
            result
        )

        return result

    def recover(
        self,
        execution: Dict[str, Any],
    ):
        result = {
            "recovered": True,
            "execution": execution,
        }

        self._history.append(
            result
        )

        return result

    def escalate(
        self,
        execution: Dict[str, Any],
    ):
        result = {
            "escalated": True,
            "execution": execution,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
