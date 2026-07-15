from autonomous.credentials.intelligence.memory_consolidator import (
    IntelligenceMemoryConsolidator,
)


def test_memory():

    result = IntelligenceMemoryConsolidator().consolidate(
        [
            {
                "signal": "authorization_consent_required",
                "confidence": 0.83,
            },
            {
                "signal": "authorization_consent_required",
                "confidence": 0.72,
            },
        ]
    )

    assert result["observations"] == 2
    assert result["dominant_signal"] == "authorization_consent_required"
    assert result["mode"] == "read_only"
