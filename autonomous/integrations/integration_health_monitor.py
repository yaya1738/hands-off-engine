"""
Integration Health Monitor

Checks all external connectors and reports status.
"""

import json
from pathlib import Path

from autonomous.integrations.registry import IntegrationRegistry


class IntegrationHealthMonitor:

    def __init__(self):
        self.log_file = Path("data/integration_health.json")

    def check(self):

        status = IntegrationRegistry().status()

        failures = []
        pending = []

        for name, item in status.items():

            if not isinstance(item, dict):
                continue

            if item.get("error"):
                failures.append({
                    "integration": name,
                    "reason": item["error"]
                })
                continue

            # OAuth providers:
            # missing token means setup pending, not system failure
            if (
                item.get("provider") == "gmail"
                and "token_present" in item
            ):
                if not item.get("token_present"):
                    pending.append({
                        "integration": name,
                        "reason": "oauth_setup_required"
                    })
                continue

            if item.get("connected") is False:
                failures.append({
                    "integration": name,
                    "reason": "not_connected"
                })

            elif item.get("token_present") is False:
                failures.append({
                    "integration": name,
                    "reason": "missing_token"
                })

        actions = []

        for item in pending:
            if item["reason"] == "oauth_setup_required":
                actions.append({
                    "integration": item["integration"],
                    "action": "add_google_oauth_credentials_json"
                })

        report = {
            "integrations": status,
            "failures": failures,
            "pending_setup": pending,
            "recommended_actions": actions,
            "healthy": len(failures) == 0,
        }

        self.log_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.log_file.write_text(
            json.dumps(report, indent=2)
        )

        return report


if __name__ == "__main__":

    monitor = IntegrationHealthMonitor()

    print(
        json.dumps(
            monitor.check(),
            indent=2
        )
    )
