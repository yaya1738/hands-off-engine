from typing import Any, Dict, List


class FactoryStrategyEvolution:
    def __init__(self):
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self.active_strategy = None
        self._history: List[Dict[str, Any]] = []

    def register_strategy(
        self,
        name: str,
        strategy: Dict[str, Any],
    ):
        self.strategies[name] = strategy

        result = {
            "registered": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def evaluate_strategy(
        self,
        name: str,
        metrics: Dict[str, Any],
    ):
        result = {
            "evaluated": True,
            "strategy": name,
            "metrics": metrics,
        }

        self._history.append(result)

        return result

    def replace_strategy(
        self,
        old: str,
        new: str,
    ):
        result = {
            "replaced": True,
            "old": old,
            "new": new,
        }

        self._history.append(result)

        return result

    def activate_strategy(
        self,
        name: str,
    ):
        self.active_strategy = name

        result = {
            "activated": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
