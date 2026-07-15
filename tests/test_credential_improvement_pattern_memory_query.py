from autonomous.credentials.intelligence.improvement_pattern_memory_query import (
    IntelligenceImprovementPatternMemoryQuery,
)


def test_query():

    result = IntelligenceImprovementPatternMemoryQuery().query(
        "prioritize_pattern_feedback_learning",
        [
            {
                "recommendation":
                "prioritize_pattern_feedback_learning"
            }
        ],
    )

    assert result["query"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["matches"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
