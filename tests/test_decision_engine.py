from ai.factory.decision_engine import (
    FactoryDecisionEngine,
)


def test_recover():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "health": "DOWN",
        }
    )

    assert result["decision"] == "RECOVER"


def test_improve():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "success_rate": 0.5,
        }
    )

    assert result["decision"] == "IMPROVE"


def test_continue():
    engine = FactoryDecisionEngine()

    result = engine.decide(
        {
            "success_rate": 1,
        }
    )

    assert result["decision"] == "CONTINUE"


def test_history():
    engine = FactoryDecisionEngine()

    engine.decide({})

    assert len(engine.history()) == 1
