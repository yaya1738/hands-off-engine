from autonomous.credentials.intelligence.improvement_pattern_context_enhancer import (
    IntelligenceImprovementPatternContextEnhancer,
)


def test_context():

    result = IntelligenceImprovementPatternContextEnhancer().enhance(
        "pattern_feedback_available",
        {
            "query":
            "pattern_feedback_consolidated",
            "reliability": 1.0,
        }
    )

    assert result["signal"] == (
        "pattern_feedback_available"
    )
    assert result["historical_match"] == (
        "pattern_feedback_consolidated"
    )
    assert result["context_quality"] == (
        "enhanced"
    )
    assert result["mode"] == "read_only"
