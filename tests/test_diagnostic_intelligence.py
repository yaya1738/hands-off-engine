from ai.factory.diagnostic_intelligence import (
    FactoryDiagnosticIntelligence,
)


def build():
    return FactoryDiagnosticIntelligence()


def test_analyze_execution():
    engine = build()

    result = engine.analyze_execution({})

    assert result["analyzed"] is True


def test_detect_failure_patterns():
    engine = build()

    result = engine.detect_failure_patterns([])

    assert result["detected"] is True


def test_explain_run():
    engine = build()

    result = engine.explain_run([])

    assert result["explained"] is True


def test_generate_recommendations():
    engine = build()

    result = engine.generate_recommendations({})

    assert result["generated"] is True


def test_history():
    engine = build()

    engine.analyze_execution({})

    assert len(engine.history()) == 1
