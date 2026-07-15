from ai.factory.recommendation_engine import (
    FactoryRecommendationEngine,
)


def test_empty_recommendation():
    engine = FactoryRecommendationEngine()

    result = engine.recommend(
        {}
    )

    assert result["recommendation"] == "NONE"


def test_recommend_pattern():
    engine = FactoryRecommendationEngine()

    result = engine.recommend(
        {
            "restart fixes scheduler": 5,
        }
    )

    assert "restart fixes scheduler" in (
        result["recommendation"]
    )


def test_rank():
    engine = FactoryRecommendationEngine()

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


def test_history():
    engine = FactoryRecommendationEngine()

    engine.recommend({})

    assert len(engine.history()) == 1
