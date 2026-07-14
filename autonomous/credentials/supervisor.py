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
        self.identity_file = Path("data/credentials/state.json")
        self.registry_file = Path("state/credentials/registry.json")

    def _load_identities(self):

        identities = {}

        # Provider metadata
        if self.identity_file.exists():
            data = json.loads(
                self.identity_file.read_text()
            )

            identities.update(data)

        # Lifecycle reality
        if self.registry_file.exists():
            registry = json.loads(
                self.registry_file.read_text()
            )

            for identity, state in registry.items():
                if identity in identities:
                    identities[identity]["lifecycle_state"] = state["state"]
                else:
                    identities[identity] = {
                        "identity": identity,
                        "provider": identity,
                        "lifecycle_state": state["state"],
                    }

        return list(identities.values())

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
