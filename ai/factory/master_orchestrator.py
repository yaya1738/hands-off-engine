from typing import Any, Dict, List


class FactoryMasterOrchestrator:
    def __init__(
        self,
        control_plane=None,
        loop=None,
        evolution=None,
    ):
        self.control_plane = control_plane
        self.loop = loop
        self.evolution = evolution
        self.running = False
        self._history: List[Dict[str, Any]] = []

    def start(self):
        self.running = True

        if self.control_plane:
            self.control_plane.start()

        result = {
            "status": "STARTED",
        }

        self._history.append(result)

        return result

    def run(
        self,
        state: Dict[str, Any],
    ):
        result = {}

        if self.loop:
            result["cycle"] = (
                self.loop.run_cycle(
                    state
                )
            )

        if self.evolution:
            result["evolution"] = (
                self.evolution.evolve(
                    state
                )
            )

        self._history.append(result)

        return result

    def evolve(
        self,
        metrics: Dict[str, Any],
    ):
        if self.evolution:
            result = self.evolution.evolve(
                metrics
            )

        else:
            result = {
                "status": "NO_EVOLUTION",
            }

        self._history.append(result)

        return result

    def status(self):
        return {
            "running": self.running,
        }

    def history(self):
        return self._history
