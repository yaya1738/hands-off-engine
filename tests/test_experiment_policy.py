from ai.factory.experiment_policy import (
    FactoryExperimentPolicy,
)


def test_safe_experiment():
    policy = FactoryExperimentPolicy()

    policy.add_rule(
        "scheduler_tuning",
        lambda ctx: True,
    )

    result = policy.evaluate(
        "scheduler_tuning"
    )

    assert result["permission"] == "SAFE"


def test_block_experiment():
    policy = FactoryExperimentPolicy()

    policy.add_rule(
        "dangerous_change",
        lambda ctx: False,
    )

    result = policy.evaluate(
        "dangerous_change"
    )

    assert result["permission"] == "BLOCK"


def test_review_default():
    policy = FactoryExperimentPolicy()

    result = policy.evaluate(
        "unknown"
    )

    assert result["permission"] == "REVIEW"


def test_history():
    policy = FactoryExperimentPolicy()

    policy.evaluate(
        "test",
    )

    assert len(policy.history()) == 1
