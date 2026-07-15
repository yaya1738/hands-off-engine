from autonomous.credentials.intelligence.outcome_resolver import (
    IntelligenceOutcomeResolver,
)


def test_resolve():

    result = IntelligenceOutcomeResolver().resolve(
        {
            "forecast": "continued_high_risk_pattern"
        },
        "continued_high_risk_pattern",
    )

    assert result["accuracy"] is True
    assert result["confidence_update"] == 0.85
    assert result["mode"] == "read_only"
