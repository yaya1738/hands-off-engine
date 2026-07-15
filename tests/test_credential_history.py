from autonomous.credentials.intelligence.history import (
    IntelligenceHistory,
)


def test_history():

    history = IntelligenceHistory(
        "state/intelligence/test_history.jsonl"
    )

    result = history.append(
        {
            "system":
            "credential_bridge",
            "confidence":
            0.83
        }
    )

    records = history.read()

    assert result["confidence"] == 0.83
    assert records[0]["system"] == "credential_bridge"
