from typing import Any, Dict, List


class FactoryConfigurationManagement:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []

    def set_config(
        self,
        key: str,
        value: Any,
    ):
        self.config[key] = value

        result = {
            "set": True,
            "key": key,
            "value": value,
        }

        self._history.append(result)

        return result

    def get_config(
        self,
        key: str,
    ):
        result = {
            "found": key in self.config,
            "value": self.config.get(key),
        }

        self._history.append(result)

        return result

    def update_config(
        self,
        updates: Dict[str, Any],
    ):
        self.config.update(updates)

        result = {
            "updated": True,
            "updates": updates,
        }

        self._history.append(result)

        return result

    def validate_config(self):
        result = {
            "valid": True,
            "keys": list(self.config.keys()),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
