from typing import Any, Dict, List


class FactoryVersionIntelligence:
    def __init__(self):
        self.versions: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_version(
        self,
        component: str,
        version: str,
    ):
        self.versions.setdefault(
            component,
            []
        ).append(version)

        result = {
            "registered": True,
            "component": component,
            "version": version,
        }

        self._history.append(result)

        return result

    def compare_versions(
        self,
        component: str,
    ):
        result = {
            "compared": True,
            "component": component,
            "versions": self.versions.get(
                component,
                []
            ),
        }

        self._history.append(result)

        return result

    def validate_upgrade(
        self,
        component: str,
        version: str,
    ):
        result = {
            "validated": True,
            "component": component,
            "version": version,
        }

        self._history.append(result)

        return result

    def rollback_version(
        self,
        component: str,
    ):
        result = {
            "rolled_back": True,
            "component": component,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
