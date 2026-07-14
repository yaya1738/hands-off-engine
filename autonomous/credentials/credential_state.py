from enum import Enum


class CredentialStatus(str, Enum):
    MISSING = "missing"
    AWAITING_AUTHORIZATION = "awaiting_authorization"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"
    REVOKED = "revoked"


class CredentialState:

    def __init__(
        self,
        identity,
        provider,
        capabilities,
        status=CredentialStatus.MISSING,
    ):
        self.identity = identity
        self.provider = provider
        self.capabilities = capabilities
        self.status = status

    def to_dict(self):
        return {
            "identity": self.identity,
            "provider": self.provider,
            "capabilities": self.capabilities,
            "status": self.status.value,
        }
