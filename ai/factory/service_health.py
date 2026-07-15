from typing import Any, Dict, List


class FactoryServiceHealth:
    def __init__(
        self,
        service=None,
    ):
        self.service = service
        self._history: List[Dict[str, Any]] = []

    def heartbeat(self):
        if self.service:
            result = self.service.heartbeat()

        else:
            result = {
                "status": "NO_SERVICE",
            }

        self._history.append(
            result
        )

        return result

    def check(self):
        heartbeat = self.heartbeat()

        result = {
            "healthy": bool(
                heartbeat.get(
                    "running",
                    heartbeat.get(
                        "active",
                        False,
                    ),
                )
            ),
            "heartbeat": heartbeat,
        }

        self._history.append(
            result
        )

        return result

    def ready(self):
        result = {
            "ready": self.check()["healthy"],
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
