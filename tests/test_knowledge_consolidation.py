from ai.factory.knowledge_consolidation import (
    FactoryKnowledgeConsolidation,
)


def build():
    return FactoryKnowledgeConsolidation()


def test_capture_pattern():
    knowledge = build()

    result = knowledge.capture_pattern(
        {
            "pattern": "SUCCESS",
        }
    )

    assert result["captured"] is True


def test_consolidate():
    knowledge = build()

    result = knowledge.consolidate()

    assert result["consolidated"] is True


def test_retrieve_knowledge():
    knowledge = build()

    knowledge.capture_pattern(
        {
            "id": 1,
        }
    )

    result = knowledge.retrieve_knowledge()

    assert len(result["knowledge"]) == 1


def test_rank_knowledge():
    knowledge = build()

    result = knowledge.rank_knowledge()

    assert result["ranked"] is True


def test_history():
    knowledge = build()

    knowledge.consolidate()

    assert len(knowledge.history()) == 1
