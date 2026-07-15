import json
from pathlib import Path
from typing import Any, Dict


class FactoryConfig:
    def __init__(
        self,
        path: str = "factory_config.json",
    ):
        self.path = Path(path)
        self._config: Dict[str, Any] = {}

    def load(self):
        if not self.path.exists():
            self._config = {}
            return self._config

        self._config = json.loads(
            self.path.read_text()
        )

        return self._config

    def get(
        self,
        key: str,
        default=None,
    ):
        return self._config.get(
            key,
            default,
        )

    def set_default(
        self,
        key: str,
        value: Any,
    ):
        if key not in self._config:
            self._config[key] = value

    def validate(self):
        return isinstance(
            self._config,
            dict,
        )
