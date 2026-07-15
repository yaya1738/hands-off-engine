from autonomous.credentials.intelligence.drift_detector import (
    IntelligenceDriftDetector,
)


def test_drift():

    result = IntelligenceDriftDetector().compare(
        {
            "confidence": 0.83,
            "situation": "attention_required",
            "diagnosis":
            "authorization_consent_required",
        },
        {
            "confidence": 0.55,
            "situation": "attention_required",
            "diagnosis":
            "authorization_consent_required",
        },
    )

    assert result["drift_detected"] is True
    assert result["mode"] == "read_only"
