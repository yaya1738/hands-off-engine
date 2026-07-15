from autonomous.credentials.intelligence.confidence import (
    AdaptiveConfidenceEngine,
)


def test_history_adjusts_confidence():

    result = AdaptiveConfidenceEngine().adjust(
        "authorization_consent_required",
        0.6,
        {
            "authorization_consent_required": {
                "count": 10,
                "successful_outcomes": 10,
            }
        }
    )

    assert result["confidence"] > 0.6
    assert result["mode"] == "read_only"
