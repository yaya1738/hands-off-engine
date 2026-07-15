from typing import Any, Dict


class FactoryShell:
    def __init__(
        self,
        controller: Any,
    ):
        self.controller = controller

    def available_commands(self):
        return [
            "status",
            "optimize",
            "state",
        ]

    def execute_command(
        self,
        command: str,
    ) -> Dict[str, Any]:

        if command == "status":
            return self.controller.inspect()

        if command == "optimize":
            return self.controller.optimize()

        if command == "state":
            return self.controller.latest_state()

        return {
            "error": "unknown_command",
            "command": command,
        }
