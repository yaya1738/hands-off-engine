from ai.factory.post_incident_learning import (
    FactoryPostIncidentLearning,
)


def test_extract():
    learner = FactoryPostIncidentLearning()

    result = learner.extract(
        {
            "lesson": "restart fixed scheduler",
        }
    )

    assert result["lesson"] == (
        "restart fixed scheduler"
    )
    assert result["source"] == "incident"


def test_store():
    learner = FactoryPostIncidentLearning()

    result = learner.store(
        {
            "lesson": "test",
        }
    )

    assert result["lesson"] == "test"


def test_learn():
    learner = FactoryPostIncidentLearning()

    result = learner.learn(
        {
            "lesson": "recovered",
        }
    )

    assert result["confidence"] == 0.9


def test_history():
    learner = FactoryPostIncidentLearning()

    learner.learn(
        {
            "lesson": "test",
        }
    )

    assert len(learner.history()) == 1
