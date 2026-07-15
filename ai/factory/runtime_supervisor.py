from typing import Any, Dict, List


class FactoryRuntimeSupervisor:
    def __init__(
        self,
        recovery=None,
    ):
        self.recovery = recovery
        self._history: List[Dict[str, Any]] = []

    def monitor(
        self,
        components: Dict[str, Any],
    ):
        result = {
            "components": components,
            "healthy": all(
                components.values()
            ),
        }

        self._history.append(
            result
        )

        return result

    def detect(
        self,
        status: Dict[str, Any],
    ):
        result = {
            "failure": not status.get(
                "healthy",
                False,
            ),
        }

        self._history.append(
            result
        )

        return result

    def recover(
        self,
    ):
        if self.recovery:
            result = self.recovery.restore()

        else:
            result = {
                "status": "NO_RECOVERY",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
