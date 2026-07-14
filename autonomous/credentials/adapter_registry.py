"""
Hands-Off Credential Adapter Registry
"""

from autonomous.credentials.adapters.gmail import GmailCredentialAdapter


class CredentialAdapterRegistry:

    def __init__(self):
        self.adapters = {}
        self.recovery_adapters = {}

        self.register(
            GmailCredentialAdapter()
        )

    def register(self, adapter):
        self.adapters[adapter.provider()] = adapter

        if hasattr(adapter, "recover"):
            self.recovery_adapters[adapter.provider()] = adapter

    def get(self, provider):
        return self.adapters.get(provider)

    def get_recovery(self, provider):
        return self.recovery_adapters.get(provider)

    def status(self):
        return list(self.adapters.keys())

    def recovery_status(self):
        return list(self.recovery_adapters.keys())
