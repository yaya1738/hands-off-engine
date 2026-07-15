from autonomous.credentials.intelligence.improvement_context_enhancer import (
    IntelligenceImprovementContextEnhancer,
)


def test_context():

    result = IntelligenceImprovementContextEnhancer().enhance(
        "confidence_decline",
        [
            {
                "knowledge":
                "increase_pattern_confidence_tracking",
                "reliability": 1.0,
            }
        ],
    )

    assert result["historical_match"] == (
        "increase_pattern_confidence_tracking"
    )
    assert result["context_quality"] == "enhanced"
    assert result["mode"] == "read_only"
