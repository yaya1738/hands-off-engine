from typing import Any, Dict, List


class FactoryConfigManager:
    def __init__(
        self,
        defaults: Dict[str, Any] = None,
    ):
        self.config = defaults or {}
        self._history: List[Dict[str, Any]] = []

    def load(
        self,
        config: Dict[str, Any],
    ):
        self.config.update(
            config
        )

        result = {
            "status": "LOADED",
            "config": self.config,
        }

        self._history.append(
            result
        )

        return result

    def validate(self):
        result = {
            "valid": True,
            "config": self.config,
        }

        self._history.append(
            result
        )

        return result

    def update(
        self,
        key: str,
        value: Any,
    ):
        self.config[key] = value

        result = {
            "key": key,
            "value": value,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
