"""
Credential-aware integration heartbeat.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add repo root to Python path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from credential_integration_bridge import run as credential_bridge


def heartbeat():

    bridge = credential_bridge()

    failures = []

    integration = bridge.get("integration", {})

    for failure in integration.get("failures", []):

        identity = failure.get("integration")

        action = next(
            (
                x["action"]
                for x in bridge.get("actions", [])
                if x["identity"] == identity
            ),
            "unknown"
        )

        failures.append({
            "integration": identity,
            "reason": failure.get("reason"),
            "credential_action": action,
        })

    return {
        "healthy": len(failures) == 0,
        "failures": failures,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            heartbeat(),
            indent=2
        )
    )
