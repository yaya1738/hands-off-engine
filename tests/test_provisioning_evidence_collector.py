from ai.audit.provisioning_evidence_collector import (
    ProvisioningEvidenceCollector,
)


def test_complete_evidence_bundle():
    collector = ProvisioningEvidenceCollector()

    result = collector.collect(
        provenance={},
        decision={},
        policy={},
        integrity={},
        timeline=[],
    )

    assert result["complete"] is True
    assert result["missing"] == []


def test_missing_evidence_detected():
    collector = ProvisioningEvidenceCollector()

    result = collector.collect(
        provenance={},
        decision={},
    )

    assert result["complete"] is False
    assert "policy" in result["missing"]
