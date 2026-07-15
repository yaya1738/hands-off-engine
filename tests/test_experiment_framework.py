from ai.factory.experiment_framework import (
    FactoryExperimentFramework,
)


def test_create_experiment():
    framework = FactoryExperimentFramework()

    exp = framework.create_experiment(
        "test_change",
        lambda: "ok",
    )

    assert exp["status"] == "CREATED"


def test_run_experiment():
    framework = FactoryExperimentFramework()

    exp = framework.create_experiment(
        "test_change",
        lambda: "ok",
    )

    result = framework.run(exp)

    assert result["status"] == "COMPLETED"
    assert result["result"] == "ok"


def test_evaluate():
    framework = FactoryExperimentFramework()

    exp = {
        "name": "good",
        "status": "COMPLETED",
    }

    result = framework.evaluate(exp)

    assert result["decision"] == "PROMOTE"


def test_history():
    framework = FactoryExperimentFramework()

    framework.create_experiment(
        "test",
        lambda: True,
    )

    assert len(framework.history()) == 1
