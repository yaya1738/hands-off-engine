from typing import Any, Dict, List


class FactoryCapabilityOnboarding:
    def __init__(self):
        self._capabilities: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def onboard(
        self,
        name: str,
        owner: str,
        steps: List[str],
        description: str = "",
    ):
        capability = {
            "name": name,
            "owner": owner,
            "steps": steps,
            "description": description,
            "status": "REGISTERED",
        }

        self._capabilities[name] = capability
        self._history.append(capability)

        return {
            "registered": True,
            "capability": capability,
        }

    def get(self, name: str):
        return self._capabilities.get(name)

    def list_capabilities(self):
        return list(self._capabilities.values())

    def verify(self, name: str):
        capability = self._capabilities.get(name)

        if not capability:
            return {
                "verified": False,
                "reason": "NOT_FOUND",
            }

        return {
            "verified": True,
            "capability": name,
            "owner": capability["owner"],
            "steps": capability["steps"],
        }

    def history(self):
        return self._history
