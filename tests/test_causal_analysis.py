from ai.factory.causal_analysis import (
    FactoryCausalAnalysis,
)


def build():
    return FactoryCausalAnalysis()


def test_record_cause():
    analysis = build()

    result = analysis.record_cause(
        {
            "event": "CHANGE",
        }
    )

    assert result["recorded"] is True


def test_record_effect():
    analysis = build()

    result = analysis.record_effect(
        {
            "result": "SUCCESS",
        }
    )

    assert result["recorded"] is True


def test_analyze_relationship():
    analysis = build()

    result = analysis.analyze_relationship(
        {},
        {},
    )

    assert result["analyzed"] is True


def test_predict_outcome():
    analysis = build()

    result = analysis.predict_outcome(
        {}
    )

    assert result["predicted"] is True


def test_history():
    analysis = build()

    analysis.record_cause({})

    assert len(analysis.history()) == 1
