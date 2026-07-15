from datetime import datetime, timezone
from typing import Any, Dict, List


class FactoryCommandHistory:
    def __init__(self):
        self._commands: List[Dict[str, Any]] = []

    def record(
        self,
        command: str,
        params: Dict[str, Any],
        result: Any,
    ) -> None:
        self._commands.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "command": command,
                "params": params,
                "result": result,
            }
        )

    def all(self) -> List[Dict[str, Any]]:
        return self._commands

    def find(
        self,
        command: str,
    ) -> List[Dict[str, Any]]:
        return [
            item
            for item in self._commands
            if item["command"] == command
        ]
