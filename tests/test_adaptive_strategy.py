from ai.factory.adaptive_strategy import (
    FactoryAdaptiveStrategy,
)


def build():
    return FactoryAdaptiveStrategy()


def test_create_strategy():
    strategy = build()

    result = strategy.create_strategy(
        {
            "mode": "OPTIMIZE",
        }
    )

    assert result["created"] is True


def test_evaluate_strategy():
    strategy = build()

    result = strategy.evaluate_strategy(
        {}
    )

    assert result["evaluated"] is True


def test_adapt():
    strategy = build()

    result = strategy.adapt(
        {
            "signal": "OPTIMIZE",
        }
    )

    assert result["adapted"] is True


def test_select_strategy():
    strategy = build()

    strategy.create_strategy(
        {
            "id": 1,
        }
    )

    result = strategy.select_strategy()

    assert result["selected"]["id"] == 1


def test_history():
    strategy = build()

    strategy.adapt({})

    assert len(strategy.history()) == 1
