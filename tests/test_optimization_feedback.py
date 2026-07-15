from ai.factory.optimization_feedback import (
    OptimizationFeedback,
)


def test_high_performance():
    feedback = OptimizationFeedback()

    result = feedback.build_feedback(
        {
            "success_rate": 0.95,
        }
    )

    assert result["trend"] == "healthy"
    assert result["recommendation"] == "continue"


def test_medium_performance():
    feedback = OptimizationFeedback()

    result = feedback.build_feedback(
        {
            "success_rate": 0.7,
        }
    )

    assert result["recommendation"] == "review"


def test_low_performance():
    feedback = OptimizationFeedback()

    result = feedback.build_feedback(
        {
            "success_rate": 0.2,
        }
    )

    assert result["recommendation"] == "improve"
