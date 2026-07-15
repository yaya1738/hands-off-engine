from ai.factory.decision_policy import (
    FactoryDecisionPolicy,
)


def test_allow_decision():
    policy = FactoryDecisionPolicy()

    policy.add_rule(
        "RECOVER",
        lambda ctx: True,
    )

    result = policy.evaluate(
        "RECOVER"
    )

    assert result["permission"] == "ALLOW"


def test_block_decision():
    policy = FactoryDecisionPolicy()

    policy.add_rule(
        "EXECUTE",
        lambda ctx: False,
    )

    result = policy.evaluate(
        "EXECUTE"
    )

    assert result["permission"] == "BLOCK"


def test_review_default():
    policy = FactoryDecisionPolicy()

    result = policy.evaluate(
        "UNKNOWN"
    )

    assert result["permission"] == "REVIEW"


def test_history():
    policy = FactoryDecisionPolicy()

    policy.evaluate(
        "TEST"
    )

    assert len(policy.history()) == 1
