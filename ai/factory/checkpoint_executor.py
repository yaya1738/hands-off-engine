from typing import Any, Dict, List


class FactoryCheckpointExecutor:
    def __init__(
        self,
        audit=None,
    ):
        self.audit = audit
        self._history: List[Dict[str, Any]] = []

    def execute(
        self,
        checkpoint_decision: Dict[str, Any],
    ):
        state = checkpoint_decision.get(
            "state"
        )

        action = checkpoint_decision.get(
            "action"
        )

        if (
            state == "READY_TO_COMMIT"
            and action == "CREATE_CHECKPOINT"
        ):
            result = {
                "status": "CHECKPOINT_CREATED",
                "state": "COMPLETED",
            }

        elif state == "REVIEW_REQUIRED":
            result = {
                "status": "WAITING",
                "state": "REVIEW_REQUIRED",
            }

        elif state == "BLOCKED":
            result = {
                "status": "STOPPED",
                "state": "BLOCKED",
            }

        else:
            result = {
                "status": "ERROR",
                "state": "RECOVERY_REQUIRED",
            }

        self._history.append(
            {
                "input": checkpoint_decision,
                "result": result,
            }
        )

        if self.audit:
            self.audit.record(
                {
                    "type": "checkpoint_execution",
                    "result": result,
                }
            )

        return result

    def history(self):
        return self._history
