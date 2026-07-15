from typing import Any, Dict, List


class FactoryEvolutionCoordinator:
    def __init__(
        self,
        feedback=None,
        optimizer=None,
    ):
        self.feedback = feedback
        self.optimizer = optimizer
        self._history: List[Dict[str, Any]] = []

    def evaluate(
        self,
        metrics: Dict[str, Any],
    ):
        result = {
            "metrics": metrics,
        }

        self._history.append(
            result
        )

        return result

    def upgrade(
        self,
        metrics: Dict[str, Any],
    ):
        if self.optimizer:
            return self.optimizer.optimize(
                metrics
            )

        return {
            "action": "NO_UPGRADE",
        }

    def evolve(
        self,
        metrics: Dict[str, Any],
    ):
        evaluation = self.evaluate(
            metrics
        )

        upgrade = self.upgrade(
            metrics
        )

        result = {
            "evaluation": evaluation,
            "upgrade": upgrade,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
