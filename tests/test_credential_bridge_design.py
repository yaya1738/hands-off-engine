"""
Credential Bridge Design Tests

These tests define the intended contract.
They are not production patches.
"""

from autonomous.credentials.transition import (
    CredentialState,
    can_transition,
)


def test_existing_authorization_transition():
    assert can_transition(
        CredentialState.REQUESTED,
        CredentialState.AWAITING_AUTHORIZATION,
    )


def test_recovery_bridge_requirement():
    """
    Expected future bridge:
    RECOVERY -> AWAITING_AUTHORIZATION

    Current system may fail until bridge is implemented.
    """
    assert can_transition(
        CredentialState.RECOVERY,
        CredentialState.AWAITING_AUTHORIZATION,
    )


def test_required_components_exist():
    from autonomous.credentials.credential_request import CredentialRequest
    from autonomous.credentials.adapter_registry import CredentialAdapterRegistry

    request = CredentialRequest(
        capability="gmail",
        provider="gmail",
    )

    assert request.provider == "gmail"

    registry = CredentialAdapterRegistry()

    adapter = registry.get("gmail")

    assert adapter is not None
    assert hasattr(adapter, "acquire")
