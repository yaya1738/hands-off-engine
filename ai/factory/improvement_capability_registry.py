from typing import Any, Callable, Dict, List


class FactoryImprovementCapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, Callable] = {}
        self._history: List[Dict[str, Any]] = []

    def register(
        self,
        name: str,
        handler: Callable,
    ):
        self._capabilities[name] = handler

        result = {
            "registered": True,
            "capability": name,
        }

        self._history.append(result)

        return result

    def resolve(
        self,
        name: str,
    ):
        return self._capabilities.get(name)

    def list_capabilities(self):
        return list(self._capabilities.keys())

    def status(self):
        return {
            "count": len(self._capabilities),
            "capabilities": self.list_capabilities(),
        }

    def history(self):
        return self._history
