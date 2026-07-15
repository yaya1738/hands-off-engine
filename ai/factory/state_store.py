import json
from pathlib import Path
from typing import Any, Dict


class FactoryStateStore:
    def __init__(
        self,
        path="factory_state.json",
    ):
        self.path = Path(path)

    def save(
        self,
        state: Dict[str, Any],
    ):
        self.path.write_text(
            json.dumps(
                state,
                indent=2,
                default=str,
            )
        )

        return state

    def load(self):
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text()
        )

    def clear(self):
        if self.path.exists():
            self.path.unlink()

        return True

    def snapshot(self):
        return self.load()
