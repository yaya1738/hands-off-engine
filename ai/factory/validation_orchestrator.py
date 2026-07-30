from typing import Any, Dict, List
import traceback


class FactoryValidationOrchestrator:
    def __init__(
        self,
        validator=None,
    ):
        self.validator = validator
        self._history: List[Dict[str, Any]] = []

    def run_validation(self):
        try:
            if self.validator is None:
                return self._record({
                    "status": "ERROR",
                    "state": "RECOVERY_REQUIRED",
                    "errors": [
                        "validator_missing"
                    ],
                    "failed_checks": [],
                })

            result = self.validator()

            if not isinstance(result, dict):
                return self._record({
                    "status": "ERROR",
                    "state": "RECOVERY_REQUIRED",
                    "errors": [
                        "invalid_validator_response"
                    ],
                    "failed_checks": [],
                })

            status = result.get(
                "status",
                "ERROR",
            )

            if status == "PASS":
                state = "READY_FOR_COMMIT"
            elif status == "FAIL":
                state = "BLOCKED"
            else:
                state = "RECOVERY_REQUIRED"

            failed_checks = result.get(
                "failed_checks",
                [],
            )

            errors = result.get(
                "errors",
                [],
            )

            report = {
                "status": status,
                "state": state,
                "failed_checks": failed_checks,
                "errors": errors,
                "source": result,
            }

            return self._record(report)

        except Exception as error:
            return self._record({
                "status": "ERROR",
                "state": "RECOVERY_REQUIRED",
                "failed_checks": [],
                "errors": [
                    str(error),
                    traceback.format_exc(),
                ],
            })

    def _record(self, result):
        self._history.append(result)
        return result

    def history(self):
        return self._history
