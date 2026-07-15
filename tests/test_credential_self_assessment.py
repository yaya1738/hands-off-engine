from autonomous.credentials.intelligence.self_assessment import (
    IntelligenceSelfAssessment,
)


def test_assessment():

    result = IntelligenceSelfAssessment().assess(
        0.72,
        0.67,
        "declining",
    )

    assert result["intelligence_score"] == 0.69
    assert result["mode"] == "read_only"
