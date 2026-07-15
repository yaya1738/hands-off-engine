from ai.factory.knowledge_graph_intelligence import (
    FactoryKnowledgeGraphIntelligence,
)


def build():
    return FactoryKnowledgeGraphIntelligence()


def test_add_node():
    engine = build()

    result = engine.add_node(
        "a",
        {}
    )

    assert result["added"] is True


def test_add_relationship():
    engine = build()

    result = engine.add_relationship(
        "a",
        "b",
        "related",
    )

    assert result["linked"] is True


def test_traverse_graph():
    engine = build()

    result = engine.traverse_graph(
        "a"
    )

    assert result["traversed"] is True


def test_find_connections():
    engine = build()

    result = engine.find_connections(
        "a"
    )

    assert result["found"] is True


def test_history():
    engine = build()

    engine.add_node(
        "x",
        {}
    )

    assert len(engine.history()) == 1
