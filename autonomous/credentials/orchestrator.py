"""
Hands-Off Credential Recovery Orchestrator
"""

from autonomous.credentials.adapter_registry import CredentialAdapterRegistry
from autonomous.credentials.recovery_executor import CredentialRecoveryExecutor
from autonomous.credentials.lifecycle import CredentialLifecycle


class CredentialOrchestrator:

    def __init__(self):
        self.registry = CredentialAdapterRegistry()
        self.executor = CredentialRecoveryExecutor(
            self.registry
        )
        self.lifecycle = CredentialLifecycle()

    def monitor_and_recover(self, provider, identity):
        health = self.lifecycle.health_check(identity)

        if health["healthy"]:
            return {
                "action": "none",
                "health": health,
            }

        decision = self.lifecycle.recovery_check(identity)

        if decision["action"] != "begin_recovery":
            return decision

        result = self.executor.execute(
            provider,
            identity,
        )

        return {
            "health": health,
            "decision": decision,
            "recovery": result,
        }
