from autonomous.credentials.intelligence.pattern_learning import (
    PatternLearningEngine,
)


def test_pattern_learning():

    result = PatternLearningEngine().analyse(
        [
            {
                "diagnosis":
                "authorization_consent_required",
                "outcome":
                "resolved",
            },
            {
                "diagnosis":
                "authorization_consent_required",
                "outcome":
                "resolved",
            },
        ]
    )

    assert result[
        "authorization_consent_required"
    ]["reliability"] == 1.0
