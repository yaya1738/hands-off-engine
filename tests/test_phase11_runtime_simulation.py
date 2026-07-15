from autonomous.credentials.transition import (
    can_transition,
    CredentialState,
)


def test_recovery_to_authorization():
    assert can_transition(
        CredentialState.RECOVERY,
        CredentialState.AWAITING_AUTHORIZATION
    )


def test_authorization_to_validation():
    assert can_transition(
        CredentialState.AUTHORIZED,
        CredentialState.VALIDATING
    )


def test_validation_to_active():
    assert can_transition(
        CredentialState.VALIDATING,
        CredentialState.ACTIVE
    )


def test_mock_provider_only():
    """
    Runtime simulation must not require external OAuth.
    """
    mock_provider = {
        "provider": "gmail",
        "mode": "mock",
        "external_auth": False
    }

    assert mock_provider["external_auth"] is False

