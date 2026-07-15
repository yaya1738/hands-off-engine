from ai.factory.forecasting_intelligence import (
    FactoryForecastingIntelligence,
)


def build():
    return FactoryForecastingIntelligence()


def test_create_forecast():
    engine = build()

    result = engine.create_forecast(
        {}
    )

    assert result["created"] is True


def test_analyze_pattern():
    engine = build()

    result = engine.analyze_pattern(
        {}
    )

    assert result["analyzed"] is True


def test_predict_state():
    engine = build()

    result = engine.predict_state(
        {}
    )

    assert result["predicted"] is True


def test_evaluate_accuracy():
    engine = build()

    result = engine.evaluate_accuracy(
        {}
    )

    assert result["evaluated"] is True


def test_history():
    engine = build()

    engine.create_forecast(
        {}
    )

    assert len(engine.history()) == 1
