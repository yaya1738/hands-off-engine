from ai.factory.experimentation_engine import (
    FactoryExperimentationEngine,
)


def build():
    return FactoryExperimentationEngine()


def test_create_experiment():
    engine = build()

    result = engine.create_experiment(
        "test",
        {}
    )

    assert result["created"] is True


def test_run_trial():
    engine = build()

    result = engine.run_trial(
        "test",
        {}
    )

    assert result["run"] is True


def test_compare_results():
    engine = build()

    result = engine.compare_results(
        []
    )

    assert result["compared"] is True


def test_select_winner():
    engine = build()

    result = engine.select_winner(
        []
    )

    assert result["selected"] is True


def test_history():
    engine = build()

    engine.create_experiment(
        "x",
        {}
    )

    assert len(engine.history()) == 1
