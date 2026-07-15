from typing import Any, Dict, List


class FactoryResourceAllocator:
    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.allocations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def resource_registry(
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

    def estimate_cost(
        self,
        task: Dict[str, Any],
    ):
        result = {
            "estimated": True,
            "cost": 1,
            "task": task,
        }

        self._history.append(result)

        return result

    def allocate_resources(
        self,
        task: Dict[str, Any],
        amount: int = 1,
    ):
        allocation = {
            "task": task,
            "amount": amount,
        }

        self.allocations.append(allocation)

        result = {
            "allocated": True,
            "allocation": allocation,
        }

        self._history.append(result)

        return result

    def rebalance(
        self,
        allocations: List[Dict[str, Any]],
    ):
        result = {
            "rebalanced": True,
            "count": len(allocations),
        }

        self._history.append(result)

        return result

    def measure_efficiency(
        self,
        outcome: Dict[str, Any],
    ):
        result = {
            "measured": True,
            "efficiency": 1,
            "outcome": outcome,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
