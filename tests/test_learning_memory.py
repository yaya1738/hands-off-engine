from ai.factory.learning_memory import (
    FactoryLearningMemory,
)


def test_store():
    memory = FactoryLearningMemory()

    result = memory.store(
        {
            "action": "IMPROVE",
        }
    )

    assert result["action"] == "IMPROVE"


def test_recall():
    memory = FactoryLearningMemory()

    memory.store(
        {
            "decision": "RECOVER",
        }
    )

    result = memory.recall(
        "decision",
        "RECOVER",
    )

    assert len(result) == 1


def test_patterns():
    memory = FactoryLearningMemory()

    memory.store(
        {
            "action": "IMPROVE",
        }
    )

    result = memory.patterns()

    assert result["IMPROVE"] == 1


def test_history():
    memory = FactoryLearningMemory()

    memory.store({})

    assert len(memory.history()) == 1
