"""
Hands-Off Credential Supervisor

Runs credential health cycles.
"""

from autonomous.credentials.orchestrator import CredentialOrchestrator


class CredentialSupervisor:

    def __init__(self):
        self.orchestrator = CredentialOrchestrator()

    def check(self, provider, identity):
        return self.orchestrator.monitor_and_recover(
            provider,
            identity,
        )

    def check_all(self, identities):
        results = []

        for item in identities:
            results.append(
                self.check(
                    item["provider"],
                    item["identity"],
                )
            )

        return results
