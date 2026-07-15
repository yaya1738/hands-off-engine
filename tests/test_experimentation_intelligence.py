from ai.factory.experimentation_intelligence import (
    FactoryExperimentationIntelligence,
)


def build():
    return FactoryExperimentationIntelligence()


def test_create_experiment():
    engine = build()

    result = engine.create_experiment(
        {}
    )

    assert result["created"] is True


def test_run_experiment():
    engine = build()

    result = engine.run_experiment(
        {}
    )

    assert result["run"] is True


def test_evaluate_experiment():
    engine = build()

    result = engine.evaluate_experiment(
        {}
    )

    assert result["evaluated"] is True


def test_promote_result():
    engine = build()

    result = engine.promote_result(
        {}
    )

    assert result["promoted"] is True


def test_history():
    engine = build()

    engine.create_experiment(
        {}
    )

    assert len(engine.history()) == 1
