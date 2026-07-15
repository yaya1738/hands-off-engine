from autonomous.credentials.intelligence.response_planner import (
    IntelligenceResponsePlanner,
)


def test_response():

    result = IntelligenceResponsePlanner().plan(
        "high",
        0.9,
        [
            "confidence_shift",
            "health_degraded",
        ],
    )

    assert result["response"] == "human_review_priority"
    assert result["priority"] == 90
    assert result["mode"] == "read_only"
