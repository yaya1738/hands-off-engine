from typing import Any, Dict, List


class FactoryResourceAllocator:
    """Bounded resource accounting; allocation requests fail closed on exhaustion."""

    def __init__(self, max_allocation_amount: int = 1, max_outstanding_allocations: int = 64):
        if max_allocation_amount < 1 or max_outstanding_allocations < 1:
            raise ValueError("resource limits must be positive")
        self.max_allocation_amount = max_allocation_amount
        self.max_outstanding_allocations = max_outstanding_allocations
        self.resources: Dict[str, Any] = {}
        self.allocations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def resource_registry(self, name: str, resource: Dict[str, Any]):
        self.resources[name] = resource
        result = {"registered": True, "resource": name}
        self._history.append(result)
        return result

    def estimate_cost(self, task: Dict[str, Any]):
        result = {"estimated": True, "cost": 1, "task": task}
        self._history.append(result)
        return result

    def allocate_resources(self, task: Dict[str, Any], amount: int = 1):
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
            raise ValueError("allocation amount must be a positive integer")
        if amount > self.max_allocation_amount:
            raise ValueError("allocation amount exceeds configured limit")
        if len(self.allocations) >= self.max_outstanding_allocations:
            raise RuntimeError("resource allocation capacity exhausted")

        allocation = {"task": task, "amount": amount}
        self.allocations.append(allocation)
        result = {"allocated": True, "allocation": allocation}
        self._history.append(result)
        return result

    def rebalance(self, allocations: List[Dict[str, Any]]):
        result = {"rebalanced": True, "count": len(allocations)}
        self._history.append(result)
        return result

    def measure_efficiency(self, outcome: Dict[str, Any]):
        result = {"measured": True, "efficiency": 1, "outcome": outcome}
        self._history.append(result)
        return result

    def history(self):
        return self._history
