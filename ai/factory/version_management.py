from typing import Any, Dict, List


class FactoryVersionManagement:
    def __init__(self):
        self.versions: Dict[str, Dict[str, Any]] = {}
        self.current_version = None
        self._history: List[Dict[str, Any]] = []

    def create_version(
        self,
        version: str,
        data: Dict[str, Any],
    ):
        self.versions[version] = data

        result = {
            "created": True,
            "version": version,
        }

        self._history.append(result)

        return result

    def compare_versions(
        self,
        version_a: str,
        version_b: str,
    ):
        result = {
            "compared": True,
            "from": version_a,
            "to": version_b,
        }

        self._history.append(result)

        return result

    def rollback_version(
        self,
        version: str,
    ):
        self.current_version = version

        result = {
            "rolled_back": True,
            "version": version,
        }

        self._history.append(result)

        return result

    def promote_version(
        self,
        version: str,
    ):
        self.current_version = version

        result = {
            "promoted": True,
            "version": version,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
