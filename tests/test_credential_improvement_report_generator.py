from autonomous.credentials.intelligence.improvement_report_generator import (
    IntelligenceImprovementReportGenerator,
)


def test_report():

    result = IntelligenceImprovementReportGenerator().generate(
        {
            "recommendation":
            "prioritize_confidence_tracking",
            "confidence": 0.85,
            "priority": "medium",
        }
    )

    assert result["status"] == "stable"
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
