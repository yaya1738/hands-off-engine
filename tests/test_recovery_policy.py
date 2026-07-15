from ai.factory.recovery_policy import (
    FactoryRecoveryPolicy,
)


def test_safe_recovery():
    policy = FactoryRecoveryPolicy()

    policy.add_rule(
        "scheduler",
        lambda ctx: True,
    )

    result = policy.evaluate(
        "scheduler"
    )

    assert result["permission"] == "SAFE"


def test_block_recovery():
    policy = FactoryRecoveryPolicy()

    policy.add_rule(
        "database",
        lambda ctx: False,
    )

    result = policy.evaluate(
        "database"
    )

    assert result["permission"] == "BLOCK"


def test_history():
    policy = FactoryRecoveryPolicy()

    policy.evaluate(
        "unknown"
    )

    assert len(policy.history()) == 1
