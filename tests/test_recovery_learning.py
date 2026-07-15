from ai.factory.recovery_learning import (
    FactoryRecoveryLearning,
)


def test_analyze():
    learning = FactoryRecoveryLearning()

    result = learning.analyze(
        [
            {
                "status": "RECOVERED",
            },
            {
                "status": "FAILED",
            },
        ]
    )

    assert result["total_recoveries"] == 2
    assert result["successful"] == 1
    assert result["failed"] == 1


def test_success_rate():
    learning = FactoryRecoveryLearning()

    rate = learning.success_rate(
        [
            {
                "status": "RECOVERED",
            }
        ]
    )

    assert rate == 1


def test_recommend():
    learning = FactoryRecoveryLearning()

    result = learning.recommend(
        [
            {
                "status": "RECOVERED",
            }
        ]
    )

    assert result == "allow_auto_recovery"
