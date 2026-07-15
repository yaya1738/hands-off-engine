from autonomous.credentials.intelligence.decision_summary import (
    IntelligenceDecisionSummary,
)


def test_summary():

    result = IntelligenceDecisionSummary().summarize(
        "human_review_priority",
        "high",
        0.69,
        0.81,
        90,
    )

    assert result["decision"] == "human_review_priority"
    assert result["risk"] == "high"
    assert result["priority"] == 90
    assert result["mode"] == "read_only"
