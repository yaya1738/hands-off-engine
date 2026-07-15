import json
from pathlib import Path


class IntelligenceReplayEngine:

    def __init__(
        self,
        path="state/intelligence/archive.jsonl"
    ):
        self.path = Path(path)

    def replay(self):

        if not self.path.exists():
            return {
                "records": 0,
                "mode": "read_only",
            }

        records = [
            json.loads(line)
            for line in self.path.read_text()
            .splitlines()
            if line.strip()
        ]

        situations = [
            item["context"].get("situation")
            for item in records
        ]

        return {
            "records":
                len(records),
            "situations":
                situations,
            "mode":
                "read_only",
        }
