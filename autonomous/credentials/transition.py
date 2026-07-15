"""
Hands-Off Credential Transition Guard

Single authority for credential state movement.
No module should mutate credential state directly.
"""

from enum import Enum


class CredentialTransitionError(Exception):
    """Raised when an invalid credential state transition is attempted."""
    pass


class CredentialState(str, Enum):
    REQUESTED = "REQUESTED"
    AWAITING_AUTHORIZATION = "AWAITING_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    VALIDATING = "VALIDATING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RECOVERY = "RECOVERY"


_ALLOWED_TRANSITIONS = {
    CredentialState.REQUESTED: {
        CredentialState.AWAITING_AUTHORIZATION,
    },
    CredentialState.AWAITING_AUTHORIZATION: {
        CredentialState.AUTHORIZED,
    },
    CredentialState.AUTHORIZED: {
        CredentialState.VALIDATING,
    },
    CredentialState.VALIDATING: {
        CredentialState.ACTIVE,
    },
    CredentialState.ACTIVE: {
        CredentialState.EXPIRED,
    },
    CredentialState.EXPIRED: {
        CredentialState.RECOVERY,
    },
    CredentialState.RECOVERY: {
        CredentialState.AWAITING_AUTHORIZATION,
        CredentialState.VALIDATING,
    },
}


def can_transition(current, target):
    """
    Check whether a state transition is allowed.
    """

    current = CredentialState(current)
    target = CredentialState(target)

    return target in _ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(current, target):
    """
    Enforce lifecycle rules.
    """

    if not can_transition(current, target):
        raise CredentialTransitionError(
            f"Invalid credential transition: {current} -> {target}"
        )

    return True
