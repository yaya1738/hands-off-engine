from typing import Any, Dict, List


class FactoryImprovementRuntime:
    def __init__(
        self,
        orchestrator,
    ):
        self.orchestrator = orchestrator
        self.running = False
        self._history: List[Dict[str, Any]] = []

    def run_once(
        self,
        metrics: Dict[str, Any],
    ):
        result = self.orchestrator.run_cycle(
            metrics
        )

        self._history.append(
            result
        )

        return result

    def start(
        self,
        metrics: Dict[str, Any],
    ):
        self.running = True

        return self.run_once(
            metrics
        )

    def stop(self):
        self.running = False

        return {
            "status": "STOPPED",
        }

    def history(self):
        return self._history
