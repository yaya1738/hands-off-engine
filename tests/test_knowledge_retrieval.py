from ai.factory.knowledge_retrieval import (
    FactoryKnowledgeRetrieval,
)


def build():
    return FactoryKnowledgeRetrieval(
        [
            {
                "pattern": "SUCCESS",
            }
        ]
    )


def test_search():
    retrieval = build()

    result = retrieval.search(
        "SUCCESS"
    )

    assert len(result["matches"]) == 1


def test_match_context():
    retrieval = build()

    result = retrieval.match_context(
        {}
    )

    assert result["matched"] is True


def test_recommend():
    retrieval = build()

    result = retrieval.recommend()

    assert result["recommendation"] is not None


def test_empty_recommend():
    retrieval = FactoryKnowledgeRetrieval()

    result = retrieval.recommend()

    assert result["recommendation"] is None


def test_history():
    retrieval = build()

    retrieval.search(
        "SUCCESS"
    )

    assert len(retrieval.history()) == 1
