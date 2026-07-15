import json
from pathlib import Path


class CredentialEventCollector:

    def __init__(self, path="state/audit/credentials.jsonl"):
        self.path = Path(path)

    def load_events(self):
        events = []

        if not self.path.exists():
            return events

        for line in self.path.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                continue

        return events

    def normalize(self, event):
        return {
            "identity": event.get("identity"),
            "from": event.get("from"),
            "to": event.get("to"),
            "reason": event.get("reason"),
            "timestamp": event.get("timestamp"),
        }
