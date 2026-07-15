from autonomous.credentials.intelligence.correlation import (
    CredentialCorrelationEngine,
)


def test_detects_cluster():

    result = CredentialCorrelationEngine().analyze(
        [
            {
                "diagnosis":
                "authorization_consent_required"
            },
            {
                "diagnosis":
                "authorization_consent_required"
            },
            {
                "diagnosis":
                "authorization_consent_required"
            },
        ]
    )

    assert len(result) == 1
    assert result[0]["mode"] == "read_only"
