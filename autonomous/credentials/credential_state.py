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


import json
from pathlib import Path
from datetime import datetime, timezone


class CredentialStateStore:
    """
    Persistent credential reality store.

    Lifecycle uses this as the source of current state.
    """

    def __init__(
        self,
        path="state/credentials/registry.json",
    ):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load_all(self):
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

    def get(self, identity):
        return self.load_all().get(identity)

    def save(self, identity, state):
        data = self.load_all()

        data[identity] = {
            "state": state,
            "updated": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self.path.write_text(
            json.dumps(
                data,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data[identity]
