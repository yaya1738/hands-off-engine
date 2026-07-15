from autonomous.credentials.intelligence.memory_retrieval import (
    IntelligenceMemoryRetrieval,
)


def test_retrieval():

    result = IntelligenceMemoryRetrieval().retrieve(
        [
            {
                "signal": "authorization_consent_required",
                "confidence": 0.83,
            },
            {
                "signal": "authorization_consent_required",
                "confidence": 0.79,
            },
        ],
        "authorization_consent_required",
    )

    assert result["matches"] == 2
    assert result["historical_confidence"] == 0.81
    assert result["mode"] == "read_only"
