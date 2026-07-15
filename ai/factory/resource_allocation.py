from typing import Any, Dict, List


class FactoryResourceAllocation:
    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.allocations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def register_resource(
        self,
        name: str,
        value: Any,
    ):
        self.resources[name] = value

        result = {
            "registered": True,
            "resource": name,
        }

        self._history.append(
            result
        )

        return result

    def allocate(
        self,
        resource: str,
        goal: Dict[str, Any],
    ):
        allocation = {
            "resource": resource,
            "goal": goal,
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

    def rebalance(self):
        result = {
            "rebalanced": True,
            "allocation_count": len(
                self.allocations
            ),
        }

        self._history.append(
            result
        )

        return result

    def availability(self):
        result = {
            "resources": self.resources,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
