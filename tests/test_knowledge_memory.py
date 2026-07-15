from ai.factory.knowledge_memory import (
    FactoryKnowledgeMemory,
)


def test_store():
    memory = FactoryKnowledgeMemory()

    result = memory.store(
        "restart fixes scheduler",
        "recovery",
        0.9,
    )

    assert result["lesson"] == (
        "restart fixes scheduler"
    )


def test_query():
    memory = FactoryKnowledgeMemory()

    memory.store(
        "scheduler restart works",
        "recovery",
    )

    result = memory.query(
        "scheduler"
    )

    assert len(result) == 1


def test_learn():
    memory = FactoryKnowledgeMemory()

    count = memory.learn(
        [
            {
                "lesson": "test lesson",
            }
        ]
    )

    assert count == 1


def test_snapshot():
    memory = FactoryKnowledgeMemory()

    memory.store(
        "lesson",
        "test",
    )

    assert len(memory.snapshot()) == 1
