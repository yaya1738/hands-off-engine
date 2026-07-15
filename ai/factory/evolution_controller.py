from typing import Any, Dict, List


class FactoryEvolutionController:
    def __init__(
        self,
        improvement=None,
    ):
        self.improvement = improvement
        self.version = 0
        self._history: List[Dict[str, Any]] = []

    def evaluate_change(
        self,
        change: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "change": change,
        }

        self._history.append(
            result
        )

        return result

    def approve(
        self,
        change: Dict[str, Any],
    ):
        result = {
            "approved": True,
            "change": change,
        }

        self._history.append(
            result
        )

        return result

    def apply(
        self,
        change: Dict[str, Any],
    ):
        self.version += 1

        result = {
            "status": "APPLIED",
            "version": self.version,
            "change": change,
        }

        self._history.append(
            result
        )

        return result

    def rollback(self):
        if self.version > 0:
            self.version -= 1

        result = {
            "status": "ROLLED_BACK",
            "version": self.version,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
