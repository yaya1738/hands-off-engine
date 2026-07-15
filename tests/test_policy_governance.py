from ai.factory.policy_governance import (
    FactoryPolicyGovernance,
)


def build():
    return FactoryPolicyGovernance()


def test_create_policy():
    engine = build()

    result = engine.create_policy(
        "safety",
        {}
    )

    assert result["created"] is True


def test_evaluate_policy():
    engine = build()

    result = engine.evaluate_policy(
        "safety",
        {}
    )

    assert result["evaluated"] is True


def test_enforce_policy():
    engine = build()

    result = engine.enforce_policy(
        "safety",
        {}
    )

    assert result["enforced"] is True


def test_update_policy():
    engine = build()

    result = engine.update_policy(
        "safety",
        {}
    )

    assert result["updated"] is True


def test_history():
    engine = build()

    engine.create_policy(
        "x",
        {}
    )

    assert len(engine.history()) == 1
