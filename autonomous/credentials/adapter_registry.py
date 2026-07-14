from autonomous.credentials.adapters.gmail import GmailCredentialAdapter


class CredentialAdapterRegistry:

    def __init__(self):
        self.adapters = {}

        self.register(
            GmailCredentialAdapter()
        )

    def register(self, adapter):
        self.adapters[adapter.provider()] = adapter

    def get(self, provider):
        return self.adapters.get(provider)

    def status(self):
        return list(self.adapters.keys())
