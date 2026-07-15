from typing import Any, Dict


class FactoryDecisionContext:
    def __init__(self):
        self._signals: Dict[str, Any] = {}

    def add_signal(
        self,
        name: str,
        value: Any,
    ):
        self._signals[name] = value

    def build(self):
        return dict(
            self._signals
        )

    def snapshot(self):
        return {
            "signals": dict(
                self._signals
            )
        }
