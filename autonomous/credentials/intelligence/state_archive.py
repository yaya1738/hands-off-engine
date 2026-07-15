import json
from pathlib import Path
from datetime import datetime, timezone


class IntelligenceStateArchive:

    def __init__(
        self,
        path="state/intelligence/archive.jsonl"
    ):
        self.path = Path(path)

    def archive(self, context, validation):

        record = {
            "archive_id":
                "intel_" +
                datetime.now(
                    timezone.utc
                ).strftime("%Y%m%d%H%M%S"),

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "validated":
                validation.get(
                    "valid",
                    False
                ),

            "context":
                context,

            "mode":
                "read_only",
        }

        with self.path.open("a") as f:
            f.write(
                json.dumps(record)
                + "\n"
            )

        return record

    def read(self):

        if not self.path.exists():
            return []

        return [
            json.loads(line)
            for line in self.path.read_text()
            .splitlines()
            if line.strip()
        ]
