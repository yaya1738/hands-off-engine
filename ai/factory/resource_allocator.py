from typing import Any, Dict, List


class FactoryResourceAllocator:
    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.allocations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def request(
        self,
        resource: Dict[str, Any],
    ):
        self.resources.update(
            resource
        )

        result = {
            "requested": True,
            "resource": resource,
        }

        self._history.append(
            result
        )

        return result

    def allocate(
        self,
        target: Dict[str, Any],
    ):
        result = {
            "allocated": True,
            "target": target,
        }

        self.allocations.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def prioritize(
        self,
        requests: List[Dict[str, Any]],
    ):
        result = {
            "priority": (
                requests[0]
                if requests
                else None
            ),
        }

        self._history.append(
            result
        )

        return result

    def utilization(self):
        result = {
            "resources": len(
                self.resources
            ),
            "allocations": len(
                self.allocations
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
