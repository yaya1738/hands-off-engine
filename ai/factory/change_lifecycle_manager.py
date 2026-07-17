from ai.factory.validation_runner import FactoryValidationRunner

from typing import Any, Dict, List


class FactoryChangeLifecycleManager:
    def __init__(self):
        self.changes: List[Dict[str, Any]] = []
        self.validation_runner = FactoryValidationRunner()
        self._history: List[Dict[str, Any]] = []

    def start_change(
        self,
        change: Dict[str, Any],
    ):
        entry = {
            "status": "started",
            "change": change,
            "validation": [],
        }

        self.changes.append(entry)
        self._history.append(entry)

        return entry

    def record_validation(
        self,
        change_id: Any,
        validation: Dict[str, Any],
    ):
        for change in self.changes:
            if change.get("change", {}).get("id") == change_id:
                change["validation"].append(validation)

                self._history.append(change)

                return change

        result = {
            "updated": False,
            "change_id": change_id,
        }

        self._history.append(result)

        return result

    def complete_change(
        self,
        change_id: Any,
    ):
        for change in self.changes:
            if change.get("change", {}).get("id") == change_id:
                change["status"] = "completed"

                self._history.append(change)

                return change

        result = {
            "completed": False,
            "change_id": change_id,
        }

        self._history.append(result)

        return result

    def validate_change(
        self,
        change: Dict[str, Any],
    ):
        result = self.validation_runner.validate_change(
            change
        )

        self._history.append(
            result
        )

        return result

    def report(self):
        return {
            "changes": self.changes,
            "count": len(self.changes),
        }

    def history(self):
        return self._history
