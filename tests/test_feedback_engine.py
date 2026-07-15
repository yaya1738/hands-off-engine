from ai.factory.feedback_engine import (
    FactoryFeedbackEngine,
)
from ai.factory.learning_memory import (
    FactoryLearningMemory,
)


def test_analyze():
    memory = FactoryLearningMemory()

    memory.store(
        {
            "action": "IMPROVE",
        }
    )

    engine = FactoryFeedbackEngine(
        memory
    )

    result = engine.analyze()

    assert result["patterns"]["IMPROVE"] == 1


def test_score():
    engine = FactoryFeedbackEngine()

    result = engine.score(
        {
            "success": True,
        }
    )

    assert result["score"] == 1


def test_recommend():
    memory = FactoryLearningMemory()

    memory.store(
        {
            "action": "IMPROVE",
        }
    )

    engine = FactoryFeedbackEngine(
        memory
    )

    result = engine.recommend()

    assert (
        result["recommendation"]
        == "OPTIMIZE_IMPROVEMENT_FLOW"
    )


def test_history():
    engine = FactoryFeedbackEngine()

    engine.analyze()

    assert len(engine.history()) == 1
