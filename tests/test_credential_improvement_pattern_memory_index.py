from autonomous.credentials.intelligence.improvement_pattern_memory_index import (
    IntelligenceImprovementPatternMemoryIndex,
)


def test_index():

    result = IntelligenceImprovementPatternMemoryIndex().build(
        [
            {
                "event":
                "improvement_pattern_recommendation_generated"
            }
        ]
    )

    assert result["index"] == (
        "improvement_pattern_recommendations"
    )
    assert result["entries"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
