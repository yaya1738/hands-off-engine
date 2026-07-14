"""
Hands-Off Credential Audit Log

Records every credential lifecycle transition.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class CredentialAudit:
    """
    Append-only credential lifecycle audit writer.
    """

    def __init__(self, path="state/audit/credentials.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        identity,
        from_state,
        to_state,
        reason,
    ):
        event = {
            "identity": identity,
            "from": str(from_state),
            "to": str(to_state),
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return event


    def read_all(self):
        if not self.path.exists():
            return []

        return [
            json.loads(line)
            for line in self.path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
