import json
from pathlib import Path
from datetime import datetime, timezone


class IntelligenceEventBus:

    def __init__(
        self,
        path="state/intelligence/events.jsonl"
    ):
        self.path = Path(path)

    def emit(self, event_type, payload):

        event = {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "event_type":
                event_type,
            "payload":
                payload,
            "mode":
                "read_only",
        }

        with self.path.open("a") as f:
            f.write(
                json.dumps(event)
                + "\n"
            )

        return event

    def read(self):

        if not self.path.exists():
            return []

        return [
            json.loads(line)
            for line in self.path.read_text()
            .splitlines()
            if line.strip()
        ]
