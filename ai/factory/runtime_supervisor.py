from typing import Any, Dict, List


class FactoryRuntimeSupervisor:
    def __init__(
        self,
        runtime,
    ):
        self.runtime = runtime
        self._history: List[Dict[str, Any]] = []

    def check(self):
        status = {
            "running": self.runtime.running,
        }

        self._history.append(
            status
        )

        return status

    def monitor(self):
        status = self.check()

        if not status["running"]:
            return {
                "action": "RESTART_REQUIRED",
                "status": status,
            }

        return {
            "action": "HEALTHY",
            "status": status,
        }

    def recover(self):
        if not self.runtime.running:
            self.runtime.running = True

            result = {
                "action": "RECOVERED",
            }

        else:
            result = {
                "action": "NO_ACTION",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
