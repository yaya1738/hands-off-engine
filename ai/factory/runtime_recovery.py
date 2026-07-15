from typing import Any, Dict, List


class FactoryRuntimeRecovery:
    def __init__(
        self,
        runtime=None,
        state=None,
    ):
        self.runtime = runtime
        self.state = state
        self._history: List[Dict[str, Any]] = []

    def restart(self):
        if self.runtime:
            self.runtime.running = True

        result = {
            "action": "RESTART",
            "status": "SUCCESS",
        }

        self._history.append(
            result
        )

        return result

    def restore(self):
        state = {}

        if self.state:
            state = self.state.restore()

        result = {
            "action": "RESTORE",
            "state": state,
        }

        self._history.append(
            result
        )

        return result

    def recover(
        self,
        alert: Dict[str, Any],
    ):
        level = alert.get(
            "level"
        )

        if level == "CRITICAL":
            return self.restart()

        if level == "WARNING":
            return self.restore()

        result = {
            "action": "NO_ACTION",
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
