"""
Hands-Off Integration Supervisor

Continuously monitors external connectors.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from autonomous.integrations.integration_health_monitor import IntegrationHealthMonitor


class IntegrationSupervisor:

    def __init__(self):
        self.events = Path("data/integration_events.jsonl")
        self.monitor = IntegrationHealthMonitor()

    def run_once(self):

        report = self.monitor.check()

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "healthy": report["healthy"],
            "integrations": report["integrations"],
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
