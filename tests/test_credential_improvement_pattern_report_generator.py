from autonomous.credentials.intelligence.improvement_pattern_report_generator import (
    IntelligenceImprovementPatternReportGenerator,
)


def test_report():

    result = IntelligenceImprovementPatternReportGenerator().generate(
        {
            "recommendation":
            "prioritize_pattern_feedback_learning",
            "confidence":
            0.85,
            "priority":
            "medium",
        }
    )

    assert result["system"] == (
        "improvement_pattern_intelligence"
    )
    assert result["status"] == "stable"
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
