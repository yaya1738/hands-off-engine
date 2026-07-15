from ai.factory.decision_intelligence import (
    FactoryDecisionIntelligence,
)


def build():
    return FactoryDecisionIntelligence()


def test_create_decision():
    engine = build()

    result = engine.create_decision(
        {}
    )

    assert result["created"] is True


def test_evaluate_options():
    engine = build()

    result = engine.evaluate_options(
        []
    )

    assert result["evaluated"] is True


def test_score_decision():
    engine = build()

    result = engine.score_decision(
        {}
    )

    assert result["scored"] is True


def test_select_action():
    engine = build()

    result = engine.select_action(
        []
    )

    assert result["selected"] is True


def test_history():
    engine = build()

    engine.create_decision(
        {}
    )

    assert len(engine.history()) == 1
