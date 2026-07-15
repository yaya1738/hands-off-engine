from autonomous.credentials.intelligence.improvement_pattern_confidence_knowledge_forecast_learning_confidence_forecast_learning_confidence_forecast import (
    IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecast,
)


def test_forecast():

    result = IntelligenceImprovementPatternConfidenceKnowledgeForecastLearningConfidenceForecast().forecast(
        {
            "trend":
            "stable",
            "confidence":
            1.0,
        }
    )

    assert result["forecast"] == (
        "continued_stability"
    )
    assert result["confidence"] == 0.82
    assert "stable_trend" in result["basis"]
    assert result["mode"] == "read_only"
