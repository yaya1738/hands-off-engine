from autonomous.credentials.intelligence.state_comparator import (
    IntelligenceStateComparator,
)


def test_compare():

    result = IntelligenceStateComparator().compare(
        {
            "health": "healthy",
            "confidence": 0.9,
            "stability": 1.0,
        },
        {
            "health": "degraded",
            "confidence": 0.7,
            "stability": 0.72,
        },
    )

    assert result["trend"] == "degrading"
    assert result["mode"] == "read_only"
