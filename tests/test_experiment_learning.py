from ai.factory.experiment_learning import (
    FactoryExperimentLearning,
)


def test_analyze():
    learning = FactoryExperimentLearning()

    result = learning.analyze(
        [
            {
                "decision": "PROMOTE",
            },
            {
                "decision": "REJECT",
            },
        ]
    )

    assert result["total"] == 2
    assert result["promoted"] == 1
    assert result["rejected"] == 1


def test_success_rate():
    learning = FactoryExperimentLearning()

    rate = learning.success_rate(
        [
            {
                "decision": "PROMOTE",
            }
        ]
    )

    assert rate == 1


def test_recommend():
    learning = FactoryExperimentLearning()

    result = learning.recommend(
        [
            {
                "decision": "PROMOTE",
            }
        ]
    )

    assert result == "allow_more_tests"


def test_history():
    learning = FactoryExperimentLearning()

    learning.analyze([])

    assert len(learning.history()) == 1
