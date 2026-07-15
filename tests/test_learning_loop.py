from ai.factory.learning_loop import (
    FactoryLearningLoop,
)


def build():
    return FactoryLearningLoop()


def test_record_outcome():
    learner = build()

    result = learner.record_outcome(
        {
            "success": True,
        }
    )

    assert result["recorded"] is True


def test_analyze_feedback():
    learner = build()

    result = learner.analyze_feedback(
        {}
    )

    assert result["analyzed"] is True


def test_update_model():
    learner = build()

    result = learner.update_model(
        {}
    )

    assert result["updated"] is True


def test_generate_improvement():
    learner = build()

    result = learner.generate_improvement(
        {}
    )

    assert result["generated"] is True


def test_history():
    learner = build()

    learner.record_outcome({})

    assert len(learner.history()) == 1
