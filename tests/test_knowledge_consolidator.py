from ai.factory.knowledge_consolidator import (
    FactoryKnowledgeConsolidator,
)


def test_add_lesson():
    system = FactoryKnowledgeConsolidator()

    result = system.add_lesson(
        {
            "lesson": "restart fixes scheduler",
        }
    )

    assert result["lesson"] == (
        "restart fixes scheduler"
    )


def test_find_patterns():
    system = FactoryKnowledgeConsolidator()

    system.add_lesson(
        {
            "lesson": "restart fixes scheduler",
        }
    )

    system.add_lesson(
        {
            "lesson": "restart fixes scheduler",
        }
    )

    result = system.find_patterns()

    assert result[
        "restart fixes scheduler"
    ] == 2


def test_consolidate():
    system = FactoryKnowledgeConsolidator()

    result = system.consolidate()

    assert result["count"] == 0


def test_history():
    system = FactoryKnowledgeConsolidator()

    system.consolidate()

    assert len(system.history()) == 1
