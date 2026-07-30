from typing import Any, Dict, List


class FactoryControlPlane:
    def __init__(
        self,
        scheduler=None,
        supervisor=None,
        recovery=None,
        orchestrator=None,
    ):
        self.scheduler = scheduler
        self.supervisor = supervisor
        self.recovery = recovery
        self.orchestrator = orchestrator
        self.running = False
        self._history: List[Dict[str, Any]] = []

    def start(self):
        self.running = True

        result = {
            "status": "STARTED",
        }

        self._history.append(
            result
        )

        return result

    def cycle(
        self,
        state: Dict[str, Any],
    ):
        result = {}

        if self.supervisor:
            result["health"] = (
                self.supervisor.monitor(
                    {
                        "runtime": True,
                    }
                )
            )

        if self.scheduler:
            result["schedule"] = (
                self.scheduler.run_pending()
            )

        if self.orchestrator:
            result["orchestration"] = (
                self.orchestrator.run(
                    state
                )
            )

        self._history.append(
            result
        )

        return result

    def health(self):
        return {
            "running": self.running,
        }

    def recover(self):
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

    def inspect(self):
        return {
            "health": {
                "status": "HEALTHY"
            },
            "running": self.running,
            "history_count": len(self._history),
        }

    def save_state(self, state):
        self._latest_state = state

        result = {
            "status": "STATE_SAVED",
            "state": state,
        }

        self._history.append(result)

        return result


    def latest_state(self):
        return getattr(
            self,
            "_latest_state",
            None,
        )

    def optimize(self):
        return {
            "action": "continue",
        }

    def history(self):
        return self._history
