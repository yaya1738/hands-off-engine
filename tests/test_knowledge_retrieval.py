from ai.factory.knowledge_retrieval import (
    FactoryKnowledgeRetrieval,
)


class FakeMemory:
    def query(self, term):
        return [
            {
                "lesson": "restart scheduler",
                "confidence": 0.9,
            },
            {
                "lesson": "check logs",
                "confidence": 0.5,
            },
        ]


def test_retrieve():
    engine = FactoryKnowledgeRetrieval(
        FakeMemory()
    )

    result = engine.retrieve(
        "scheduler"
    )

    assert len(result) == 2


def test_rank():
    engine = FactoryKnowledgeRetrieval(
        FakeMemory()
    )

    result = engine.rank(
        [
            {
                "confidence": 0.2,
            },
            {
                "confidence": 0.8,
            },
        ]
    )

    assert result[0]["confidence"] == 0.8


def test_recommend():
    engine = FactoryKnowledgeRetrieval(
        FakeMemory()
    )

    result = engine.recommend(
        "scheduler"
    )

    assert result["confidence"] == 0.9
