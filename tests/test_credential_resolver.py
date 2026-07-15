from autonomous.credentials.intelligence.resolver import (
    CredentialDiagnosticResolver,
)


def test_resolver_priority():

    result = CredentialDiagnosticResolver().resolve(
        [
            {
                "diagnosis":
                "no_known_anomaly",
                "pattern":
                "normal_operation",
                "confidence":
                0.90,
            },
            {
                "diagnosis":
                "authorization_consent_required",
                "pattern":
                "authorization_consent_loop",
                "confidence":
                0.85,
            },
        ]
    )

    assert result["primary_diagnosis"] == "no_known_anomaly"
    assert result["mode"] == "read_only"
