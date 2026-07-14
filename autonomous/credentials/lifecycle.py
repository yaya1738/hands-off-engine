"""
Hands-Off Credential Lifecycle Engine

The only layer allowed to move credential states.
"""

from autonomous.credentials.transition import (
    validate_transition,
    CredentialState,
)

from autonomous.credentials.audit import CredentialAudit
from autonomous.credentials.credential_state import CredentialStateStore


class CredentialLifecycle:

    def __init__(self):
        self.audit = CredentialAudit()
        self.store = CredentialStateStore()

    def get_state(self, identity):
        existing = self.store.get(identity)

        if existing:
            return existing["state"]

        return CredentialState.REQUESTED.value

    def transition(
        self,
        identity,
        target,
        reason,
    ):
        current = self.get_state(identity)

        validate_transition(
            current,
            target,
        )

        self.store.save(
            identity,
            target,
        )

        self.audit.record(
            identity=identity,
            from_state=current,
            to_state=target,
            reason=reason,
        )

        return {
            "identity": identity,
            "from": current,
            "to": target,
            "reason": reason,
        }
