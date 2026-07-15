from ai.factory.decision_engine import (
    FactoryDecisionEngine,
)


def test_recovery_decision():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "health": "DEGRADED",
        }
    )

    assert result["decision"] == "RECOVER"


def test_escalation_decision():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "risk": "HIGH",
        }
    )

    assert result["decision"] == "ESCALATE"


def test_continue_decision():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "health": "HEALTHY",
        }
    )

    assert result["decision"] == "CONTINUE"


def test_history():
    engine = FactoryDecisionEngine()

    engine.decide({})

    assert len(engine.history()) == 1
