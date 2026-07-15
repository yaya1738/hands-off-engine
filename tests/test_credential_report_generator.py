from autonomous.credentials.intelligence.report_generator import (
    IntelligenceReportGenerator,
)


def test_report():

    result = IntelligenceReportGenerator().generate(
        "degraded",
        0.72,
        0.69,
        "human_review_recommended",
    )

    assert result["system"] == "credential_bridge"
    assert result["intelligence"]["score"] == 0.69
    assert result["mode"] == "read_only"
