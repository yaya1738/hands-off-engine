from ai.factory.learning_intelligence import (
    FactoryLearningIntelligence,
)


def build():
    return FactoryLearningIntelligence()


def test_record_experience():
    engine = build()

    result = engine.record_experience(
        {}
    )

    assert result["recorded"] is True


def test_analyze_outcome():
    engine = build()

    result = engine.analyze_outcome(
        {}
    )

    assert result["analyzed"] is True


def test_extract_lesson():
    engine = build()

    result = engine.extract_lesson(
        {}
    )

    assert result["extracted"] is True


def test_update_model():
    engine = build()

    result = engine.update_model(
        "core",
        {}
    )

    assert result["updated"] is True


def test_history():
    engine = build()

    engine.record_experience(
        {}
    )

    assert len(engine.history()) == 1
