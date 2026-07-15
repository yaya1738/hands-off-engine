from autonomous.credentials.intelligence.evidence import (
    CredentialEvidenceAnalyzer,
)


def test_evidence_analysis():

    result = CredentialEvidenceAnalyzer().analyze(
        "authorization_consent_required",
        [
            "adapter_requires_external_consent",
            "REQUESTED->AWAITING_AUTHORIZATION"
        ]
    )

    assert (
        "external_consent_requested"
        in result["supporting_evidence"]
    )

    assert result["mode"] == "read_only"
