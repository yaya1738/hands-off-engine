from typing import Any, Dict, List


class FactoryResourceManagement:
    def __init__(self):
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.allocations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def register_resource(
        self,
        name: str,
        resource: Dict[str, Any],
    ):
        self.resources[name] = resource

        result = {
            "registered": True,
            "resource": name,
        }

        self._history.append(
            result
        )

        return result

    def allocate_resource(
        self,
        name: str,
        task: Dict[str, Any],
    ):
        allocation = {
            "resource": name,
            "task": task,
        }

        self.allocations.append(
            allocation
        )

        result = {
            "allocated": True,
            "allocation": allocation,
        }

        self._history.append(
            result
        )

        return result

    def release_resource(
        self,
        name: str,
    ):
        result = {
            "released": True,
            "resource": name,
        }

        self._history.append(
            result
        )

        return result

    def check_capacity(self):
        result = {
            "capacity_available": True,
            "resources": len(
                self.resources
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
