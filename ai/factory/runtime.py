from typing import Any, Dict, List


class FactoryRuntime:
    def __init__(
        self,
        bootstrap=None,
        control_plane=None,
    ):
        self.bootstrap = bootstrap
        self.control_plane = control_plane
        self.running = False
        self.cycles = 0
        self._history: List[Dict[str, Any]] = []

    def start(self):
        if self.bootstrap:
            self.bootstrap.start()

        self.running = True

        result = {
            "status": "RUNNING",
        }

        self._history.append(
            result
        )

        return result

    def run(
        self,
        state=None,
    ):
        if not self.running:
            self.start()

        if self.control_plane:
            result = self.control_plane.cycle(
                state or {}
            )

        else:
            result = {
                "status": "NO_CONTROL_PLANE",
            }

        self.cycles += 1

        output = {
            "cycle": self.cycles,
            "result": result,
        }

        self._history.append(
            output
        )

        return output

    def stop(self):
        self.running = False

        result = {
            "status": "STOPPED",
        }

        self._history.append(
            result
        )

        return result

    def heartbeat(self):
        return {
            "running": self.running,
            "cycles": self.cycles,
        }

    def status(self):
        return self.heartbeat()

    def history(self):
        return self._history
