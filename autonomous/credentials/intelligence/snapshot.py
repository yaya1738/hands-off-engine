import json
from pathlib import Path
from datetime import datetime, timezone


class IntelligenceSnapshot:

    def create(self, digest):

        snapshot = {
            "system": "credential_bridge",
            "intelligence_version": "1.0",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "health": digest.get(
                "status",
                "unknown"
            ),
            "top_diagnosis": digest.get(
                "diagnosis"
            ),
            "confidence": digest.get(
                "confidence"
            ),
            "recommendation": digest.get(
                "recommendation"
            ),
            "safety_mode": "read_only",
        }

        Path(
            "state/intelligence/"
            "credential_bridge_snapshot.json"
        ).write_text(
            json.dumps(
                snapshot,
                indent=2
            )
        )

        return snapshot
