from ai.factory.knowledge_base import (
    FactoryKnowledgeBase,
)


class FakeMemory:
    def retrieve(self):
        return [
            {
                "pattern": "success",
            }
        ]


def build():
    return FactoryKnowledgeBase(
        FakeMemory()
    )


def test_extract():
    kb = build()

    result = kb.extract()

    assert result["patterns_found"] == 1


def test_summarize():
    kb = build()

    kb.extract()

    result = kb.summarize()

    assert result["knowledge_items"] == 1


def test_query():
    kb = build()

    kb.extract()

    result = kb.query()

    assert len(result) == 1


def test_confidence():
    kb = build()

    kb.extract()

    result = kb.confidence()

    assert result["confidence"] is True


def test_history():
    kb = build()

    kb.extract()

    assert len(kb.history()) == 1
