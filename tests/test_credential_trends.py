from autonomous.credentials.intelligence.trends import (
    CredentialTrendAnalyzer,
)


def test_trend_analysis():

    events = [
        {
            "from": "AUTHORIZED",
            "to": "VALIDATING",
            "reason": "health_check"
        },
        {
            "from": "VALIDATING",
            "to": "ACTIVE",
            "reason": "success"
        },
    ]

    result = CredentialTrendAnalyzer(). analyze(events)

    assert result["event_volume"] == 2
    assert "AUTHORIZED->VALIDATING" in result["transition_counts"]
