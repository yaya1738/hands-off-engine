"""
Hands-Off Integration Supervisor

Continuously monitors external connectors.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from autonomous.integrations.integration_health_monitor import IntegrationHealthMonitor
from credential_integration_bridge import run as credential_bridge
from autonomous.credentials.supervisor import CredentialSupervisor


class IntegrationSupervisor:

    def __init__(self):
        self.events = Path("data/integration_events.jsonl")
        self.monitor = IntegrationHealthMonitor()
        self.credentials = CredentialSupervisor()

    def run_once(self):

        report = self.monitor.check()

        credential_sync = credential_bridge()

        credential_results = self.credentials.check_all()

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "healthy": report["healthy"],
            "integrations": report["integrations"],
            "credential_sync": credential_sync,
            "credentials": credential_results,
        }

        self.events.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(self.events, "a") as f:
            f.write(json.dumps(event) + "\n")

        return event


if __name__ == "__main__":
    print(
        json.dumps(
            IntegrationSupervisor().run_once(),
            indent=2
        )
    )
