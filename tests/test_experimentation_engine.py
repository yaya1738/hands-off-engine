from ai.factory.experimentation_engine import (
    FactoryExperimentationEngine,
)


def build():
    return FactoryExperimentationEngine()


def test_create_experiment():
    engine = build()

    result = engine.create_experiment(
        {
            "name": "TEST",
        }
    )

    assert result["created"] is True


def test_run_experiment():
    engine = build()

    result = engine.run_experiment(
        {}
    )

    assert result["run"] is True


def test_measure_result():
    engine = build()

    result = engine.measure_result(
        {}
    )

    assert result["measured"] is True


def test_select_winner():
    engine = build()

    result = engine.select_winner(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["winner"]["id"] == 1


def test_history():
    engine = build()

    engine.create_experiment({})

    assert len(engine.history()) == 1
