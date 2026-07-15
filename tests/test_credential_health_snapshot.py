from autonomous.credentials.intelligence.health_snapshot import (
    IntelligenceHealthSnapshot,
)


def test_snapshot():

    result = IntelligenceHealthSnapshot().build(
        "degraded",
        0.72,
        0.83,
        "confidence_change",
        "attention_required",
        "read_only",
    )

    assert result["system"] == "credential_bridge"
    assert result["mode"] == "read_only"
