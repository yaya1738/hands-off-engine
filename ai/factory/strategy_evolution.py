from typing import Any, Dict, List


class FactoryStrategyEvolution:
    def __init__(self):
        self.strategies: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def store_strategy(
        self,
        strategy: Dict[str, Any],
    ):
        self.strategies.append(
            strategy
        )

        result = {
            "stored": True,
            "strategy": strategy,
        }

        self._history.append(
            result
        )

        return result

    def evaluate_strategy(
        self,
        strategy: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "strategy": strategy,
            "score": 1,
        }

        self._history.append(
            result
        )

        return result

    def evolve_strategy(
        self,
        strategy: Dict[str, Any],
    ):
        result = {
            "evolved": True,
            "strategy": strategy,
        }

        self._history.append(
            result
        )

        return result

    def select_strategy(self):
        result = {
            "selected": (
                self.strategies[0]
                if self.strategies
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
