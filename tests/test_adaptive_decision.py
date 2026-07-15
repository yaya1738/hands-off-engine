from ai.factory.adaptive_decision import (
    FactoryAdaptiveDecision,
)


def test_recover():
    engine = FactoryAdaptiveDecision()

    result = engine.decide(
        {
            "health": "DOWN",
        }
    )

    assert result["decision"] == "RECOVER"


def test_improve():
    engine = FactoryAdaptiveDecision()

    result = engine.decide(
        {
            "success_rate": 0.5,
        }
    )

    assert result["decision"] == "IMPROVE"


def test_learn_adjust():
    engine = FactoryAdaptiveDecision()

    engine.learn(
        {
            "recommendation":
                "OPTIMIZE_IMPROVEMENT_FLOW",
        }
    )

    result = engine.adjust()

    assert result["bias"] == 1


def test_history():
    engine = FactoryAdaptiveDecision()

    engine.decide({})

    assert len(engine.history()) == 1
