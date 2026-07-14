"""
Hands-Off Credential Health Monitor
"""

from datetime import datetime, timezone


class CredentialHealthMonitor:

    def check(self, identity, state):
        return {
            "identity": identity,
            "state": state,
            "healthy": state not in ("EXPIRED", "FAILED"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
