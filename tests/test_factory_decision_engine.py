from ai.factory.decision_engine import (
    FactoryDecisionEngine,
)


def test_continue_decision():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "recommendation": "continue",
            "performance": 0.95,
            "trend": "healthy",
        }
    )

    assert result["decision"] == "CONTINUE"
    assert result["confidence"] == 0.95


def test_optimize_decision():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "recommendation": "improve",
            "performance": 0.2,
            "trend": "poor",
        }
    )

    assert result["decision"] == "OPTIMIZE"


def test_history():
    engine = FactoryDecisionEngine()

    engine.decide(
        {
            "recommendation": "review",
        }
    )

    assert len(engine.history()) == 1
