from typing import Any, Dict


class FactoryService:
    def __init__(
        self,
        shell: Any,
    ):
        self.shell = shell

    def handle(
        self,
        command: str,
    ) -> Dict[str, Any]:
        return self.shell.execute_command(
            command
        )

    def health(self):
        return {
            "service": "factory",
            "status": "running",
        }
