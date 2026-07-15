from types import SimpleNamespace

from ai.audit.provisioning_policy_drift_detector import (
    ProvisioningPolicyDriftDetector,
)


def test_no_policy_drift():
    detector = ProvisioningPolicyDriftDetector()

    records = [
        SimpleNamespace(policy_version="v1", request_id="req-1"),
        SimpleNamespace(policy_version="v1", request_id="req-2"),
    ]

    result = detector.compare(records)

    assert result["drift_detected"] is False
    assert result["policy_versions"] == ["v1"]


def test_policy_drift_detected():
    detector = ProvisioningPolicyDriftDetector()

    records = [
        SimpleNamespace(policy_version="v1", request_id="req-1"),
        SimpleNamespace(policy_version="v2", request_id="req-2"),
    ]

    result = detector.compare(records)

    assert result["drift_detected"] is True
    assert len(result["policy_versions"]) == 2
