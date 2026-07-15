from ai.factory.decision_intelligence import (
    FactoryDecisionIntelligence,
)


def build():
    return FactoryDecisionIntelligence()


def test_analyze_options():
    intelligence = build()

    result = intelligence.analyze_options(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["analyzed"] is True


def test_score_decisions():
    intelligence = build()

    result = intelligence.score_decisions(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["scored"] is True


def test_select_action():
    intelligence = build()

    result = intelligence.select_action(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["selected"]["id"] == 1


def test_explain_decision():
    intelligence = build()

    result = intelligence.explain_decision(
        {}
    )

    assert result["explained"] is True


def test_history():
    intelligence = build()

    intelligence.analyze_options([])

    assert len(intelligence.history()) == 1
