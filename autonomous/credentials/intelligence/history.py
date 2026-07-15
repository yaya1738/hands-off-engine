import json
from pathlib import Path


class IntelligenceHistory:

    def __init__(
        self,
        path="state/intelligence/history.jsonl"
    ):
        self.path = Path(path)

    def append(self, snapshot):

        with self.path.open("a") as f:
            f.write(
                json.dumps(snapshot)
                + "\n"
            )

        return snapshot

    def read(self):

        if not self.path.exists():
            return []

        return [
            json.loads(line)
            for line in self.path.read_text()
            .splitlines()
            if line.strip()
        ]
