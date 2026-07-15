from typing import Any, Dict


class FactoryHealth:
    def check(
        self,
        registry: Any = None,
        memory: Any = None,
        state: Any = None,
    ) -> Dict[str, Any]:
        checks = {
            "registry": registry is not None,
            "memory": memory is not None,
            "state": state is not None,
        }

        healthy = all(checks.values())

        return {
            "status": "HEALTHY" if healthy else "DEGRADED",
            "checks": checks,
        }
