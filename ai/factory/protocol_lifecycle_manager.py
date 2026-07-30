from typing import Any, Dict, List


class FactoryProtocolLifecycleManager:
    def __init__(self):
        self._protocols: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_protocol(
        self,
        name: str,
        owner: str,
        purpose: str,
        verification: List[str] | None = None,
    ):
        protocol = {
            "name": name,
            "owner": owner,
            "purpose": purpose,
            "verification": verification or [],
            "status": "REGISTERED",
        }

        self._protocols[name] = protocol
        self._history.append(protocol)

        return {
            "registered": True,
            "protocol": protocol,
        }

    def verify_protocol(self, name: str):
        protocol = self._protocols.get(name)

        if not protocol:
            return {
                "verified": False,
                "reason": "NOT_FOUND",
            }

        return {
            "verified": True,
            "protocol": name,
            "owner": protocol["owner"],
            "verification": protocol["verification"],
        }

    def status(self):
        return {
            "count": len(self._protocols),
            "protocols": list(self._protocols.keys()),
        }

    def history(self):
        return self._history
