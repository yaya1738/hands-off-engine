from typing import Any, Dict, List


class FactoryStrategyManager:
    def __init__(self):
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def strategy_registry(
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
    ):
        result = {
            "evaluated": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def activate_strategy(
        self,
        name: str,
    ):
        result = {
            "activated": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def retire_strategy(
        self,
        name: str,
    ):
        result = {
            "retired": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def strategy_performance(
        self,
        name: str,
    ):
        result = {
            "measured": True,
            "strategy": name,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
