from autonomous.credentials.intelligence.improvement_pattern_memory import (
    IntelligenceImprovementPatternMemory,
)


def test_pattern():

    result = IntelligenceImprovementPatternMemory().analyze(
        [
            {
                "recommendation":
                "prioritize_confidence_tracking",
                "confidence": 0.85,
            }
        ]
    )

    assert result["pattern"] == (
        "confidence_tracking_recurrence"
    )
    assert result["occurrences"] == 1
    assert result["mode"] == "read_only"
