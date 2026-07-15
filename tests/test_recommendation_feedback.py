from ai.factory.recommendation_feedback import (
    FactoryRecommendationFeedback,
)


def build():
    return FactoryRecommendationFeedback()


def test_collect_recommendations():
    engine = build()

    result = engine.collect_recommendations({})

    assert result["collected"] is True


def test_evaluate_recommendations():
    engine = build()

    result = engine.evaluate_recommendations({})

    assert result["evaluated"] is True


def test_apply_improvement():
    engine = build()

    result = engine.apply_improvement({})

    assert result["applied"] is True


def test_track_effect():
    engine = build()

    result = engine.track_effect({})

    assert result["tracked"] is True


def test_history():
    engine = build()

    engine.collect_recommendations({})

    assert len(engine.history()) == 1
