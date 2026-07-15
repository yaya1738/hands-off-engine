from typing import Any, Dict, List


class FactoryActionOrchestrator:
    def __init__(self):
        self.actions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def register_action(
        self,
        action: Dict[str, Any],
    ):
        self.actions.append(
            action
        )

        result = {
            "registered": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def sequence(self):
        result = {
            "sequence": self.actions,
        }

        self._history.append(
            result
        )

        return result

    def coordinate(self):
        result = {
            "coordinated": True,
            "count": len(
                self.actions
            ),
        }

        self._history.append(
            result
        )

        return result

    def monitor(self):
        result = {
            "monitored": True,
            "active_actions": len(
                self.actions
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
