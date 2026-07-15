from ai.factory.policy_guard import (
    FactoryPolicyGuard,
)


def test_default_allow():
    guard = FactoryPolicyGuard()

    result = guard.check(
        "CONTINUE"
    )

    assert result["allowed"] is True


def test_block_rule():
    guard = FactoryPolicyGuard()

    guard.add_rule(
        "OPTIMIZE",
        lambda ctx: False,
    )

    result = guard.check(
        "OPTIMIZE"
    )

    assert result["allowed"] is False
    assert result["reason"] == "blocked"


def test_list_rules():
    guard = FactoryPolicyGuard()

    guard.add_rule(
        "REVIEW",
        lambda ctx: True,
    )

    assert "REVIEW" in guard.list_rules()
