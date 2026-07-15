from autonomous.credentials.intelligence.risk_scorer import (
    IntelligenceRiskScorer,
)


def test_risk():

    result = IntelligenceRiskScorer().score(
        True,
        "degraded",
        "declining",
        0.72,
    )

    assert result["risk_level"] == "high"
    assert result["risk_score"] == 0.9
    assert result["mode"] == "read_only"
