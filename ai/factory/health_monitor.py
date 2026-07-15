from typing import Any, Dict, List


class FactoryHealthMonitor:
    def __init__(
        self,
        checks: Dict[str, Any] = None,
    ):
        self.checks = checks or {}
        self._last_status = None
        self._alerts: List[str] = []

    def check(self):
        results = {}
        self._alerts = []

        for name, check in self.checks.items():
            try:
                result = check()

                results[name] = result

                if not result:
                    self._alerts.append(
                        name
                    )

            except Exception:
                results[name] = False
                self._alerts.append(
                    name
                )

        health = (
            "HEALTHY"
            if not self._alerts
            else "DEGRADED"
        )

        self._last_status = {
            "health": health,
            "checks": results,
            "issues": self._alerts,
        }

        return self._last_status

    def status(self):
        return self._last_status

    def alerts(self):
        return self._alerts
