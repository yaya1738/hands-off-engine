from types import SimpleNamespace

from ai.audit.provisioning_anomaly_detector import (
    ProvisioningAnomalyDetector,
)


def test_no_anomalies():
    detector = ProvisioningAnomalyDetector()

    result = detector.detect(
        [
            SimpleNamespace(
                requester_identity="agent",
                decision="AUDIT_ONLY",
            )
        ]
    )

    assert result["anomalies_detected"] is False


def test_repeated_denials_detected():
    detector = ProvisioningAnomalyDetector()

    result = detector.detect(
        [
            SimpleNamespace(
                requester_identity="agent",
                decision="DENY",
            ),
            SimpleNamespace(
                requester_identity="agent",
                decision="DENY",
            ),
        ]
    )

    assert result["anomalies_detected"] is True
    assert len(result["anomalies"]) == 1
