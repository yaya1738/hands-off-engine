from ai.factory.optimizer import FactoryOptimizer
from ai.factory.decision_engine import FactoryDecisionEngine
from ai.factory.policy_gate import FactoryPolicyGate


def test_optimizer_cycle():
    optimizer = FactoryOptimizer(
        FactoryDecisionEngine(),
        FactoryPolicyGate(),
    )

    result = optimizer.run_cycle(
        {
            "status": "HEALTHY",
        },
        [],
        {
            "failed": 0,
        },
    )

    assert result["decision"]["action"] == "continue"
    assert result["policy"]["approved"] is True


def test_optimizer_blocks_unknown_action():
    optimizer = FactoryOptimizer(
        FactoryDecisionEngine(),
        FactoryPolicyGate(),
    )

    result = optimizer.policy_gate.evaluate(
        {
            "action": "modify_core",
        }
    )

    assert result["approved"] is False
