from typing import Any, Dict, List


class FactoryServiceRecovery:
    def __init__(
        self,
        health=None,
        service=None,
    ):
        self.health = health
        self.service = service
        self._history: List[Dict[str, Any]] = []

    def detect(self):
        if self.health:
            result = self.health.check()

        else:
            result = {
                "healthy": False,
            }

        recovery_needed = not result.get(
            "healthy",
            False,
        )

        output = {
            "recovery_needed": recovery_needed,
            "health": result,
        }

        self._history.append(
            output
        )

        return output

    def recover(self):
        if self.service:
            result = self.service.restart()

        else:
            result = {
                "status": "NO_SERVICE",
            }

        self._history.append(
            result
        )

        return result

    def verify(self):
        if self.health:
            result = self.health.ready()

        else:
            result = {
                "ready": False,
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
