from autonomous.credentials.intelligence.improvement_pattern_learning_consolidator import (
    IntelligenceImprovementPatternLearningConsolidator,
)


def test_learning():

    result = IntelligenceImprovementPatternLearningConsolidator().consolidate(
        {
            "accuracy": 1.0,
        }
    )

    assert result["learning_event"] == (
        "pattern_feedback_consolidated"
    )
    assert result["reliability"] == 1.0
    assert result["memory_updated"] is True
    assert result["mode"] == "read_only"
