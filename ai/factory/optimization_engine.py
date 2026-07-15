from typing import Any, Dict, List


class FactoryOptimizationEngine:
    def __init__(self):
        self.signals: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def collect_signals(
        self,
        signal: Dict[str, Any],
    ):
        self.signals.append(
            signal
        )

        result = {
            "collected": True,
            "signal": signal,
        }

        self._history.append(
            result
        )

        return result

    def optimize(self):
        result = {
            "optimized": True,
            "signals": len(
                self.signals
            ),
        }

        self.improvements.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def compare_versions(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ):
        result = {
            "compared": True,
            "old": old,
            "new": new,
        }

        self._history.append(
            result
        )

        return result

    def recommend_improvement(self):
        result = {
            "recommendation": (
                "IMPROVE"
                if self.signals
                else "WAIT"
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
