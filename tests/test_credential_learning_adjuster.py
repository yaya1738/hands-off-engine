from autonomous.credentials.intelligence.learning_adjuster import (
    LearningAdjuster,
)


def test_learning_adjustment():

    result = LearningAdjuster().adjust(
        "authorization_consent_required",
        0.80,
        [
            {
                "diagnosis":
                "authorization_consent_required",
                "outcome":
                "resolved",
            }
        ],
    )

    assert result["confidence"] > 0.80
    assert result["source"] == "history_adjusted"
    assert result["mode"] == "read_only"
