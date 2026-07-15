from typing import Any, Dict, List


class FactoryConfigurationIntelligence:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.snapshots: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def load_config(
        self,
        config: Dict[str, Any],
    ):
        self.config = config

        result = {
            "loaded": True,
            "config": config,
        }

        self._history.append(result)

        return result

    def validate_config(
        self,
        config: Dict[str, Any],
    ):
        result = {
            "validated": True,
            "valid": True,
        }

        self._history.append(result)

        return result

    def update_config(
        self,
        changes: Dict[str, Any],
    ):
        self.snapshots.append(
            self.config.copy()
        )

        self.config.update(
            changes
        )

        result = {
            "updated": True,
            "changes": changes,
        }

        self._history.append(result)

        return result

    def rollback_config(self):
        if self.snapshots:
            self.config = self.snapshots.pop()

        result = {
            "rolled_back": True,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
