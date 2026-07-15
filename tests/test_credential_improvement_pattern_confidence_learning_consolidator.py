from autonomous.credentials.intelligence.improvement_pattern_confidence_learning_consolidator import (
    IntelligenceImprovementPatternConfidenceLearningConsolidator,
)


def test_consolidation():

    result = IntelligenceImprovementPatternConfidenceLearningConsolidator().consolidate(
        {
            "accuracy":
            1.0
        }
    )

    assert result["learning_event"] == (
        "forecast_feedback_consolidated"
    )
    assert result["reliability"] == 1.0
    assert result["memory_updated"] is True
    assert result["mode"] == "read_only"
