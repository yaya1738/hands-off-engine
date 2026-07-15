from typing import Any, Dict, List


class FactoryControlPlane:
    def __init__(
        self,
        runtime=None,
        resilience=None,
        state=None,
    ):
        self.runtime = runtime
        self.resilience = resilience
        self.state = state
        self.running = False
        self._history: List[Dict[str, Any]] = []

    def start(self):
        self.running = True

        result = {
            "status": "STARTED",
        }

        self._history.append(
            result
        )

        return result

    def cycle(
        self,
        metrics: Dict[str, Any],
    ):
        result = {}

        if self.runtime:
            result["runtime"] = (
                self.runtime.run_once(
                    metrics
                )
            )

        if self.state:
            result["checkpoint"] = (
                self.state.checkpoint(
                    result
                )
            )

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
            "running": self.running,
        }

    def history(self):
        return self._history
