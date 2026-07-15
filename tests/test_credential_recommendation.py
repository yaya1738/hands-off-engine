from autonomous.credentials.intelligence.recommendation import (
    RecommendationEngine,
)


def test_recommendation():

    result = RecommendationEngine().recommend(
        "authorization_consent_required",
        0.83,
        [
            "authorization_state_reached",
            "external_consent_requested",
        ],
    )

    assert result["recommendation"] == "await_user_authorization"
    assert result["priority"] == 100
    assert result["mode"] == "read_only"
