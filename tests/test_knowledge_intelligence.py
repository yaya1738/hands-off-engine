from ai.factory.knowledge_intelligence import (
    FactoryKnowledgeIntelligence,
)


def build():
    return FactoryKnowledgeIntelligence()


def test_store_knowledge():
    engine = build()

    result = engine.store_knowledge(
        "test",
        {}
    )

    assert result["stored"] is True


def test_retrieve_knowledge():
    engine = build()

    result = engine.retrieve_knowledge(
        "test"
    )

    assert result["retrieved"] is True


def test_link_knowledge():
    engine = build()

    result = engine.link_knowledge(
        "a",
        "b",
    )

    assert result["linked"] is True


def test_search_knowledge():
    engine = build()

    result = engine.search_knowledge(
        "x"
    )

    assert result["searched"] is True


def test_history():
    engine = build()

    engine.store_knowledge(
        "x",
        {}
    )

    assert len(engine.history()) == 1
