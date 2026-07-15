from typing import Any, Dict


class FactoryCommandRouter:
    def __init__(self, api: Any):
        self.api = api

    def dispatch(
        self,
        command: str,
        params: Dict[str, Any],
    ):
        if command == "status":
            return self.api.status()

        if command == "dashboard":
            return self.api.dashboard()

        if command == "run_task":
            return self.api.run_task(
                params["task_id"],
                params["goal"],
            )

        if command == "history":
            return self.api.history()

        return {
            "error": "unknown_command",
            "command": command,
        }
