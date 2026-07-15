from typing import Any, Dict, List


class FactoryBootstrap:
    def __init__(
        self,
        config=None,
        state=None,
        control_plane=None,
    ):
        self.config = config
        self.state = state
        self.control_plane = control_plane
        self.initialized = False
        self.running = False
        self._history: List[Dict[str, Any]] = []

    def initialize(self):
        self.initialized = True

        result = {
            "status": "INITIALIZED",
        }

        self._history.append(
            result
        )

        return result

    def start(self):
        if not self.initialized:
            self.initialize()

        if self.control_plane:
            self.control_plane.start()

        self.running = True

        result = {
            "status": "STARTED",
        }

        self._history.append(
            result
        )

        return result

    def shutdown(self):
        self.running = False

        result = {
            "status": "STOPPED",
        }

        self._history.append(
            result
        )

        return result

    def status(self):
        return {
            "initialized": self.initialized,
            "running": self.running,
        }

    def history(self):
        return self._history
