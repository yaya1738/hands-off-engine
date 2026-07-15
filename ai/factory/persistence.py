import json
from pathlib import Path
from typing import Any, Dict


class FactoryPersistence:
    def __init__(
        self,
        path: str = "factory_state.json",
    ):
        self.path = Path(path)

    def save(
        self,
        state: Dict[str, Any],
    ) -> None:
        self.path.write_text(
            json.dumps(
                state,
                indent=2,
            )
        )

    def load(self):
        if not self.path.exists():
            return None

        return json.loads(
            self.path.read_text()
        )

    def exists(self):
        return self.path.exists()

    def clear(self):
        if self.path.exists():
            self.path.unlink()
