class CredentialRequest:

    def __init__(
        self,
        capability,
        provider,
        identity=None,
    ):
        self.capability = capability
        self.provider = provider
        self.identity = identity or provider

    def to_dict(self):
        return {
            "capability": self.capability,
            "provider": self.provider,
            "identity": self.identity,
        }
