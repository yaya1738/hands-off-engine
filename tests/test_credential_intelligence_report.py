from autonomous.credentials.intelligence.report_runner import (
    CredentialIntelligenceReport,
)


def test_report_generation():

    report = CredentialIntelligenceReport().generate()

    assert "metrics" in report
    assert "health" in report
    assert report["system"] == "credential_bridge"
