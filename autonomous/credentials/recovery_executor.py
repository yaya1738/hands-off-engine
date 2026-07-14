"""
Hands-Off Credential Recovery Executor
"""

class CredentialRecoveryExecutor:

    def __init__(self, registry):
        self.registry = registry

    def execute(self, provider, identity):
        adapter = self.registry.get_recovery(provider)

        if not adapter:
            return {
                "success": False,
                "reason": "no_recovery_adapter",
            }

        return adapter.recover(identity)
