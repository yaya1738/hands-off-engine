from typing import Dict, List


class FactoryRegistry:
    def __init__(self):
        self._components: Dict[str, Dict[str, str]] = {}

    def register(
        self,
        name: str,
        component_type: str,
        version: str = "1.0",
    ) -> None:
        self._components[name] = {
            "type": component_type,
            "version": version,
        }

    def list_components(self) -> List[str]:
        return list(self._components.keys())

    def describe(self, name: str):
        return self._components.get(name)
