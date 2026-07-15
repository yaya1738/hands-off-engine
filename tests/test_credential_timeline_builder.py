from autonomous.credentials.intelligence.timeline_builder import (
    IntelligenceTimelineBuilder,
)


def test_timeline():

    result = IntelligenceTimelineBuilder().build(
        [
            {
                "decision": "human_review_priority",
                "risk": "high",
                "confidence": 0.69,
            }
        ]
    )

    assert result["events"] == 1
    assert result["risks"] == ["high"]
    assert result["mode"] == "read_only"
