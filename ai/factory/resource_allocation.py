from typing import Any, Dict, List


class FactoryResourceAllocation:
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

        self._history.append(result)

        return result

    def allocate_resource(
        self,
        name: str,
        allocation: Dict[str, Any],
    ):
        result = {
            "allocated": True,
            "resource": name,
            "allocation": allocation,
        }

        self.allocations.append(result)
        self._history.append(result)

        return result

    def release_resource(
        self,
        name: str,
    ):
        result = {
            "released": True,
            "resource": name,
        }

        self._history.append(result)

        return result

    def optimize_allocation(self):
        result = {
            "optimized": True,
            "resources": len(self.resources),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
