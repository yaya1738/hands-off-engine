from ai.factory.knowledge_graph import (
    FactoryKnowledgeGraph,
)


def build():
    return FactoryKnowledgeGraph()


def test_add_node():
    graph = build()

    result = graph.add_node(
        "A",
        {
            "type": "strategy",
        }
    )

    assert result["added"] is True


def test_add_relationship():
    graph = build()

    result = graph.add_relationship(
        "A",
        "B",
        "IMPROVES",
    )

    assert result["connected"] is True


def test_find_connections():
    graph = build()

    graph.add_relationship(
        "A",
        "B",
        "LINK",
    )

    result = graph.find_connections(
        "A"
    )

    assert len(result["connections"]) == 1


def test_query_graph():
    graph = build()

    result = graph.query_graph()

    assert "nodes" in result


def test_history():
    graph = build()

    graph.query_graph()

    assert len(graph.history()) == 1
