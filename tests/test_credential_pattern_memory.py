from autonomous.credentials.intelligence.pattern_memory import (
    IntelligencePatternMemory,
)


def test_memory():

    memory = IntelligencePatternMemory()

    result = memory.store(
        {
            "pattern": "repeated_high_risk_attention",
            "occurrences": 1,
            "confidence": 0.84,
        }
    )

    assert result["pattern_id"] == "repeated_high_risk_attention"
    assert result["confidence"] == 0.84
    assert result["mode"] == "read_only"
