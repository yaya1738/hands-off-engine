from ai.factory.learning_memory import (
    FactoryLearningMemory,
)


def build():
    return FactoryLearningMemory()


def test_remember():
    memory = build()

    result = memory.remember(
        {
            "action": "OPTIMIZE",
        }
    )

    assert result["stored"] is True


def test_record_outcome():
    memory = build()

    result = memory.record_outcome(
        {
            "success": True,
        }
    )

    assert result["type"] == "OUTCOME"


def test_retrieve():
    memory = build()

    memory.remember(
        {
            "mode": "AUTO",
        }
    )

    result = memory.retrieve()

    assert len(result) == 1


def test_patterns():
    memory = build()

    memory.remember({})

    result = memory.patterns()

    assert result["count"] == 1


def test_history():
    memory = build()

    memory.remember({})

    assert len(memory.history()) == 1
