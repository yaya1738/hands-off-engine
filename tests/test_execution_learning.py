from ai.factory.execution_learning import (
    FactoryExecutionLearning,
)


class FakeMemory:
    def remember(self, data):
        return True


def build():
    return FactoryExecutionLearning(
        FakeMemory()
    )


def test_capture_outcome():
    learning = build()

    result = learning.capture_outcome(
        {
            "status": "SUCCESS",
        }
    )

    assert result["captured"] is True


def test_classify_success():
    learning = build()

    result = learning.classify_result(
        {
            "status": "SUCCESS",
        }
    )

    assert result["classification"] == "SUCCESS"


def test_update_memory():
    learning = build()

    result = learning.update_memory(
        {}
    )

    assert result["memory_updated"] is True


def test_generate_signal():
    learning = build()

    learning.capture_outcome({})

    result = learning.generate_learning_signal()

    assert result["signal"] == "LEARN"


def test_history():
    learning = build()

    learning.capture_outcome({})

    assert len(learning.history()) == 1
