"""
Hands-Off Credential Supervisor

Runs credential health cycles.
"""

import json
from pathlib import Path

from autonomous.credentials.orchestrator import CredentialOrchestrator


class CredentialSupervisor:

    def __init__(self):
        self.orchestrator = CredentialOrchestrator()
        self.state_file = Path("data/credentials/state.json")

    def _load_identities(self):
        if not self.state_file.exists():
            return []

        data = json.loads(
            self.state_file.read_text()
        )

        return list(data.values())

    def check(self, provider, identity):
        return self.orchestrator.monitor_and_recover(
            provider,
            identity,
        )

    def check_all(self, identities=None):

        if identities is None:
            identities = self._load_identities()

        results = []

        for item in identities:
            results.append(
                self.check(
                    item["provider"],
                    item["identity"],
                )
            )

        return results
