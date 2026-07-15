from autonomous.credentials.intelligence.stability_scorer import (
    IntelligenceStabilityScorer,
)


def test_stability():

    result = IntelligenceStabilityScorer().score(
        {
            "drift_detected":
            True,
            "changes":
            [
                {
                    "type":
                    "confidence_change"
                }
            ],
        }
    )

    assert result["status"] == "minor_variation"
    assert result["mode"] == "read_only"
