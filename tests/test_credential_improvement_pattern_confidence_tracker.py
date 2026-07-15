from autonomous.credentials.intelligence.improvement_pattern_confidence_tracker import (
    IntelligenceImprovementPatternConfidenceTracker,
)


def test_confidence():

    result = IntelligenceImprovementPatternConfidenceTracker().track(
        [
            {
                "summary":
                "prioritize_pattern_feedback_learning",
                "confidence":
                0.85,
            }
        ]
    )

    assert result["pattern"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["confidence"] == 0.85
    assert result["history_entries"] == 1
    assert result["mode"] == "read_only"
