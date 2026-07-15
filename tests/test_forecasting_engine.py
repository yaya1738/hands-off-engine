from ai.factory.forecasting_engine import (
    FactoryForecastingEngine,
)


def build():
    return FactoryForecastingEngine()


def test_create_forecast():
    engine = build()

    result = engine.create_forecast(
        {
            "target": "GROWTH",
        }
    )

    assert result["created"] is True


def test_analyze_trends():
    engine = build()

    result = engine.analyze_trends(
        [
            {},
            {},
        ]
    )

    assert result["analyzed"] is True


def test_predict_future():
    engine = build()

    result = engine.predict_future(
        {}
    )

    assert result["predicted"] is True


def test_evaluate_accuracy():
    engine = build()

    result = engine.evaluate_accuracy(
        {},
        {},
    )

    assert result["evaluated"] is True


def test_history():
    engine = build()

    engine.create_forecast({})

    assert len(engine.history()) == 1
