from ai.factory.policy_gate import FactoryPolicyGate


def test_allowed_action():
    gate = FactoryPolicyGate()

    result = gate.evaluate(
        {
            "action": "continue",
        }
    )

    assert result["approved"] is True
    assert result["reason"] == "policy_allowed"


def test_blocked_action():
    gate = FactoryPolicyGate()

    result = gate.evaluate(
        {
            "action": "modify_core",
        }
    )

    assert result["approved"] is False
    assert result["reason"] == "policy_blocked"
