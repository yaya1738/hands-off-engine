from typing import Any, Dict, List


class FactoryExecutionLearning:
    def __init__(
        self,
        memory=None,
    ):
        self.memory = memory
        self.outcomes: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def capture_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        self.outcomes.append(
            outcome
        )

        result = {
            "captured": True,
            "outcome": outcome,
        }

        self._history.append(
            result
        )

        return result

    def classify_result(
        self,
        outcome: Dict[str, Any],
    ):
        success = (
            outcome.get("status")
            == "SUCCESS"
        )

        result = {
            "classification": (
                "SUCCESS"
                if success
                else "FAILURE"
            ),
        }

        self._history.append(
            result
        )

        return result

    def update_memory(
        self,
        outcome: Dict[str, Any],
    ):
        if self.memory:
            self.memory.remember(
                outcome
            )

        result = {
            "memory_updated": True,
        }

        self._history.append(
            result
        )

        return result

    def generate_learning_signal(self):
        result = {
            "signal": (
                "LEARN"
                if self.outcomes
                else "WAIT"
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
