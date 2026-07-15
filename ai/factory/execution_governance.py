from typing import Any, Dict, List


class FactoryExecutionGovernance:
    def __init__(
        self,
        risk_manager=None,
        executor=None,
    ):
        self.risk_manager = risk_manager
        self.executor = executor
        self._history: List[Dict[str, Any]] = []

    def submit(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "submitted": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def validate(
        self,
        action: Dict[str, Any],
    ):
        if self.risk_manager:
            result = self.risk_manager.check_constraints(
                action
            )

        else:
            result = {
                "within_constraints": False,
            }

        self._history.append(
            result
        )

        return result

    def authorize(
        self,
        action: Dict[str, Any],
    ):
        if self.risk_manager:
            result = self.risk_manager.approve(
                action
            )

        else:
            result = {
                "approved": False,
            }

        self._history.append(
            result
        )

        return result

    def execute(
        self,
        action: Dict[str, Any],
    ):
        if self.executor:
            result = self.executor(action)

        else:
            result = {
                "status": "NO_EXECUTOR",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
