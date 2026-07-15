from typing import Any, Dict, List


class FactoryService:
    def __init__(
        self,
        runtime=None,
    ):
        self.runtime = runtime
        self.active = False
        self._history: List[Dict[str, Any]] = []

    def start(self):
        if self.runtime:
            self.runtime.start()

        self.active = True

        result = {
            "status": "STARTED",
        }

        self._history.append(
            result
        )

        return result

    def stop(self):
        if self.runtime:
            self.runtime.stop()

        self.active = False

        result = {
            "status": "STOPPED",
        }

        self._history.append(
            result
        )

        return result

    def restart(self):
        self.stop()

        result = self.start()

        output = {
            "status": "RESTARTED",
            "result": result,
        }

        self._history.append(
            output
        )

        return output

    def status(self):
        return {
            "active": self.active,
        }

    def heartbeat(self):
        if self.runtime:
            return self.runtime.heartbeat()

        return {
            "active": self.active,
        }

    def history(self):
        return self._history
