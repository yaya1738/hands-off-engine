from ai.factory.causal_analysis_intelligence import (
    FactoryCausalAnalysisIntelligence,
)


def build():
    return FactoryCausalAnalysisIntelligence()


def test_record_cause():
    engine = build()

    result = engine.record_cause(
        {}
    )

    assert result["recorded"] is True


def test_analyze_relationship():
    engine = build()

    result = engine.analyze_relationship(
        {},
        {},
    )

    assert result["analyzed"] is True


def test_infer_impact():
    engine = build()

    result = engine.infer_impact(
        {}
    )

    assert result["inferred"] is True


def test_validate_causality():
    engine = build()

    result = engine.validate_causality(
        {}
    )

    assert result["validated"] is True


def test_history():
    engine = build()

    engine.record_cause(
        {}
    )

    assert len(engine.history()) == 1
