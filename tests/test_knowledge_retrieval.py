from ai.factory.knowledge_retrieval import (
    FactoryKnowledgeRetrieval,
)


class FakeKnowledge:
    def query(self, query):
        return [
            {
                "pattern": "stable",
            }
        ]


def build():
    return FactoryKnowledgeRetrieval(
        FakeKnowledge()
    )


def test_retrieve_context():
    retrieval = build()

    result = retrieval.retrieve_context()

    assert len(result["context"]) == 1


def test_match():
    retrieval = build()

    result = retrieval.match(
        {
            "context": [
                {}
            ]
        }
    )

    assert result["matched"] is True


def test_enrich():
    retrieval = build()

    result = retrieval.enrich(
        {
            "action": "RUN",
        }
    )

    assert result["enriched"] is True


def test_recommend():
    retrieval = build()

    result = retrieval.recommend()

    assert (
        result["recommendation"]
        == "USE_KNOWLEDGE"
    )


def test_history():
    retrieval = build()

    retrieval.recommend()

    assert len(retrieval.history()) == 1
