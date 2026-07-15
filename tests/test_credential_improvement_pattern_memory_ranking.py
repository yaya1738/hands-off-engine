from autonomous.credentials.intelligence.improvement_pattern_memory_ranking import (
    IntelligenceImprovementPatternMemoryRanking,
)


def test_ranking():

    result = IntelligenceImprovementPatternMemoryRanking().rank(
        [
            {
                "recommendation":
                "prioritize_pattern_feedback_learning",
                "confidence":
                0.85,
            }
        ]
    )

    assert result["ranking"][0]["pattern"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["ranking"][0]["score"] == 0.85
    assert result["mode"] == "read_only"
