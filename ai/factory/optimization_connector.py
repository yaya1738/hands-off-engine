from typing import Any, Dict, List


class FactoryOptimizationConnector:
    def __init__(
        self,
        optimizer=None,
    ):
        self.optimizer = optimizer
        self.performance: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def ingest_performance(
        self,
        result: Dict[str, Any],
    ):
        self.performance.append(
            result
        )

        output = {
            "ingested": True,
            "result": result,
        }

        self._history.append(
            output
        )

        return output

    def update_metrics(self):
        output = {
            "performance_count": len(
                self.performance
            ),
        }

        self._history.append(
            output
        )

        return output

    def generate_signal(self):
        output = {
            "signal": (
                "OPTIMIZE"
                if self.performance
                else "WAIT"
            ),
        }

        self._history.append(
            output
        )

        return output

    def history(self):
        return self._history
