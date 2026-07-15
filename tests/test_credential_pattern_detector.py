from autonomous.credentials.intelligence.pattern_detector import (
    IntelligencePatternDetector,
)


def test_pattern():

    result = IntelligencePatternDetector().detect(
        {
            "decisions": [
                "human_review_priority"
            ],
            "risks": [
                "high"
            ],
        }
    )

    assert result["pattern"] == "repeated_high_risk_attention"
    assert result["confidence"] == 0.84
    assert result["mode"] == "read_only"
