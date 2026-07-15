from typing import Any, Dict, List


class FactoryExternalInterface:
    def __init__(
        self,
        orchestrator=None,
    ):
        self.orchestrator = orchestrator
        self._history: List[Dict[str, Any]] = []

    def status(self):
        if self.orchestrator:
            result = self.orchestrator.status()

        else:
            result = {
                "status": "UNKNOWN",
            }

        self._history.append(
            {
                "request": "STATUS",
                "result": result,
            }
        )

        return result

    def execute(
        self,
        command: str,
        payload: Dict[str, Any] = None,
    ):
        payload = payload or {}

        if command == "START":
            result = self.orchestrator.start()

        elif command == "RUN":
            result = self.orchestrator.run(
                payload
            )

        else:
            result = {
                "status": "UNKNOWN_COMMAND",
            }

        self._history.append(
            {
                "request": command,
                "result": result,
            }
        )

        return result

    def request(
        self,
        command: str,
        payload: Dict[str, Any] = None,
    ):
        if command == "STATUS":
            return self.status()

        return self.execute(
            command,
            payload,
        )

    def history(self):
        return self._history
