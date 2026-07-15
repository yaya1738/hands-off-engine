from ai.factory.improvement_policy import (
    FactoryImprovementPolicy,
)


def test_allow():
    policy = FactoryImprovementPolicy()

    result = policy.evaluate(
        {
            "name": "cleanup",
            "risk": "low",
        }
    )

    assert result["decision"] == "ALLOW"


def test_review():
    policy = FactoryImprovementPolicy()

    result = policy.evaluate(
        {
            "name": "optimize",
            "risk": "medium",
        }
    )

    assert result["decision"] == "REVIEW"


def test_block():
    policy = FactoryImprovementPolicy()

    result = policy.evaluate(
        {
            "name": "dangerous_change",
            "risk": "high",
        }
    )

    assert result["decision"] == "BLOCK"


def test_history():
    policy = FactoryImprovementPolicy()

    policy.allow(
        {
            "name": "test",
        }
    )

    assert len(policy.history()) == 1
