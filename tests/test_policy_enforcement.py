from ai.factory.policy_enforcement import (
    FactoryPolicyEnforcement,
)


def build():
    return FactoryPolicyEnforcement()


def test_register_policy():
    policy = build()

    result = policy.register_policy(
        {
            "rule": "SAFE",
        }
    )

    assert result["registered"] is True


def test_evaluate_policy():
    policy = build()

    result = policy.evaluate_policy(
        {}
    )

    assert result["evaluated"] is True


def test_enforce_policy():
    policy = build()

    result = policy.enforce_policy(
        {}
    )

    assert result["enforced"] is True


def test_exceptions():
    policy = build()

    result = policy.exceptions(
        {}
    )

    assert result["exception"] is False


def test_history():
    policy = build()

    policy.register_policy({})

    assert len(policy.history()) == 1
