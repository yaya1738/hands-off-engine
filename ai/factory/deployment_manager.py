from typing import Any, Dict, List


class FactoryDeploymentManager:
    def __init__(self):
        self.version = None
        self.state = "IDLE"
        self._history: List[Dict[str, Any]] = []

    def prepare(
        self,
        version: str,
    ):
        self.version = version

        result = {
            "action": "PREPARE",
            "version": version,
            "status": "READY",
        }

        self._history.append(
            result
        )

        return result

    def deploy(self):
        self.state = "DEPLOYED"

        result = {
            "action": "DEPLOY",
            "status": self.state,
            "version": self.version,
        }

        self._history.append(
            result
        )

        return result

    def rollback(self):
        self.state = "ROLLED_BACK"

        result = {
            "action": "ROLLBACK",
            "status": self.state,
        }

        self._history.append(
            result
        )

        return result

    def status(self):
        return {
            "version": self.version,
            "state": self.state,
        }

    def history(self):
        return self._history
