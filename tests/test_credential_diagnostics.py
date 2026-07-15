from autonomous.credentials.intelligence.diagnostics import (
    CredentialDiagnosticEngine,
)


def test_diagnostic_engine():

    result = CredentialDiagnosticEngine().diagnose(
        trends={
            "reason_counts": {
                "adapter_requires_external_consent": 2
            }
        }
    )

    assert result["mode"] == "read_only"
    assert len(result["diagnostics"]) > 0
