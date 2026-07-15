from autonomous.credentials.intelligence.improvement_memory import (
    IntelligenceImprovementMemory,
)


def test_memory():

    memory = IntelligenceImprovementMemory()

    result = memory.remember(
        {
            "improvement": "increase_pattern_confidence_tracking",
            "priority": "medium",
        }
    )

    assert result["improvement_id"] == "increase_pattern_confidence_tracking"
    assert result["occurrences"] == 1
    assert result["mode"] == "read_only"
