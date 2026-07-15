from autonomous.credentials.intelligence.impact import (
    ImpactRankingEngine,
)


def test_priority_ranking():

    result = ImpactRankingEngine().rank(
        {
            "diagnosis":
            "authorization_consent_required",

            "occurrences":
            5,

            "identity_count":
            5,
        }
    )

    assert result["priority"] >= 70
    assert result["severity"] == "high"
    assert result["mode"] == "read_only"
