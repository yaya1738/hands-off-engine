from typing import Any, Dict, List


class FactoryDependencyManagement:
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_dependency(
        self,
        component: str,
        dependency: str,
    ):
        self.dependencies.setdefault(
            component,
            []
        ).append(
            dependency
        )

        result = {
            "registered": True,
            "component": component,
            "dependency": dependency,
        }

        self._history.append(result)

        return result

    def remove_dependency(
        self,
        component: str,
        dependency: str,
    ):
        if dependency in self.dependencies.get(
            component,
            []
        ):
            self.dependencies[component].remove(
                dependency
            )

        result = {
            "removed": True,
            "component": component,
            "dependency": dependency,
        }

        self._history.append(result)

        return result

    def resolve_dependencies(
        self,
        component: str,
    ):
        result = {
            "resolved": True,
            "dependencies": self.dependencies.get(
                component,
                []
            ),
        }

        self._history.append(result)

        return result

    def check_health(self):
        result = {
            "healthy": True,
            "components": len(
                self.dependencies
            ),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
