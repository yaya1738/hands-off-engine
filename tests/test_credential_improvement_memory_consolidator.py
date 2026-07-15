from autonomous.credentials.intelligence.improvement_memory_consolidator import (
    IntelligenceImprovementMemoryConsolidator,
)


def test_consolidation():

    result = IntelligenceImprovementMemoryConsolidator().consolidate(
        [
            {
                "improvement_id":
                "increase_pattern_confidence_tracking"
            }
        ],
        [
            {
                "feedback":
                "improvement_confirmed"
            }
        ],
    )

    assert result["confirmed_events"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
