import json
from pathlib import Path
from typing import Any, Dict


class FactoryStateStore:
    def __init__(self, path: str = "factory_state.json"):
        self.path = Path(path)

    def save(self, state: Dict[str, Any]) -> None:
        self.path.write_text(
            json.dumps(
                state,
                indent=2,
                default=str,
            )
        )

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text()
        )
