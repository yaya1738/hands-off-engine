from autonomous.credentials.intelligence.improvement_feedback_loop import (
    IntelligenceImprovementFeedbackLoop,
)


def test_feedback():

    result = IntelligenceImprovementFeedbackLoop().record(
        "continued_confidence_tracking_need",
        "continued_confidence_tracking_need",
    )

    assert result["feedback"] == "improvement_confirmed"
    assert result["learning_updated"] is True
    assert result["mode"] == "read_only"
