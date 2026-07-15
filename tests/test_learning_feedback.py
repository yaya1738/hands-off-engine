from ai.factory.learning_feedback import (
    FactoryLearningFeedback,
)


class FakeMemory:
    def remember(self, data):
        return True

    def record_outcome(self, data):
        return True


def build():
    return FactoryLearningFeedback(
        FakeMemory()
    )


def test_record_decision():
    feedback = build()

    result = feedback.record_decision(
        {
            "action": "OPTIMIZE",
        }
    )

    assert result["recorded"] is True


def test_record_result():
    feedback = build()

    result = feedback.record_result(
        {
            "success": True,
        }
    )

    assert result["recorded"] is True


def test_evaluate():
    feedback = build()

    feedback.record_decision({})

    result = feedback.evaluate()

    assert result["decisions"] == 1


def test_learn():
    feedback = build()

    result = feedback.learn()

    assert result["learned"] is True


def test_history():
    feedback = build()

    feedback.evaluate()

    assert len(feedback.history()) == 1
