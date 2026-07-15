from typing import Any, Dict, List


class FactoryDecisionIntegration:
    def __init__(
        self,
        optimizer=None,
        router=None,
    ):
        self.optimizer = optimizer
        self.router = router
        self._history: List[Dict[str, Any]] = []

    def evaluate(self):
        if self.optimizer:
            result = self.optimizer.analyze()

        else:
            result = {
                "status": "NO_OPTIMIZER",
            }

        self._history.append(
            result
        )

        return result

    def select(
        self,
        options: List[Dict[str, Any]],
    ):
        selected = (
            options[0]
            if options
            else None
        )

        result = {
            "selected": selected,
        }

        self._history.append(
            result
        )

        return result

    def route(
        self,
        decision: Dict[str, Any],
    ):
        if self.router:
            result = self.router(decision)

        else:
            result = {
                "status": "NO_ROUTER",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
