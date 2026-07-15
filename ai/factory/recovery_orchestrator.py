from typing import Any, Dict, List


class FactoryRecoveryOrchestrator:
    def __init__(
        self,
        state_manager=None,
        health_checker=None,
    ):
        self.state_manager = state_manager
        self.health_checker = health_checker
        self._history: List[Dict[str, Any]] = []

    def detect(
        self,
        health: Dict[str, Any],
    ):
        result = {
            "needs_recovery": (
                health.get("status") != "HEALTHY"
            ),
        }

        self._history.append(
            result
        )

        return result

    def restore(self):
        if self.state_manager:
            result = self.state_manager.load()

        else:
            result = {
                "status": "NO_STATE_MANAGER",
            }

        self._history.append(
            result
        )

        return result

    def verify(self):
        if self.health_checker:
            result = self.health_checker()

        else:
            result = {
                "status": "UNKNOWN",
            }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
