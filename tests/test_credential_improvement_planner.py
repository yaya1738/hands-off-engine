from autonomous.credentials.intelligence.improvement_planner import (
    IntelligenceImprovementPlanner,
)


def test_plan():

    result = IntelligenceImprovementPlanner().plan(
        {
            "accuracy": 1.0,
        }
    )

    assert result["improvement"] == "increase_pattern_confidence_tracking"
    assert result["priority"] == "medium"
    assert result["mode"] == "read_only"
