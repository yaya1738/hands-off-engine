"""
Integration Recovery

Creates recovery actions for failed integrations.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class IntegrationRecovery:

    def __init__(self):
        self.events = Path("data/integration_recovery.jsonl")

    def evaluate(self, heartbeat):

        actions = []

        for failure in heartbeat.get("failures", []):

            integration = failure["integration"]
            reason = failure["reason"]

            if reason == "not_connected":
                actions.append({
                    "integration": integration,
                    "action": "connect_required",
                    "priority": "high"
                })

            elif reason == "missing_token":
                actions.append({
                    "integration": integration,
                    "action": "credential_setup_required",
                    "priority": "high"
                })

            else:
                actions.append({
                    "integration": integration,
                    "action": "investigate",
                    "priority": "medium"
                })

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": actions
        }

        self.events.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(self.events, "a") as f:
            f.write(json.dumps(event) + "\n")

        return event


if __name__ == "__main__":
    from autonomous.integrations.heartbeat import heartbeat

    print(
        json.dumps(
            IntegrationRecovery().evaluate(
                heartbeat()
            ),
            indent=2
        )
    )
