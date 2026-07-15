"""
Hands-Off Credential Recovery Orchestrator
"""

from autonomous.credentials.adapter_registry import CredentialAdapterRegistry
from autonomous.credentials.recovery_executor import CredentialRecoveryExecutor
from autonomous.credentials.lifecycle import CredentialLifecycle
from autonomous.credentials.credential_request import CredentialRequest


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

        if result.get("action") == "reauthorization_required":

            self.lifecycle.transition(
                identity,
                "AWAITING_AUTHORIZATION",
                "credential_recovery_requires_authorization",
            )

            request = CredentialRequest(
                capability=provider,
                provider=provider,
                identity=identity,
            )

            adapter = self.registry.get(provider)

            if adapter:
                acquisition = adapter.acquire(
                    request.to_dict()
                )

                return {
                    "health": health,
                    "decision": decision,
                    "recovery": result,
                    "acquisition": acquisition,
                }

        return {
            "health": health,
            "decision": decision,
            "recovery": result,
        }
