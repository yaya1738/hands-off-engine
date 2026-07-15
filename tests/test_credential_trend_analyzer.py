from autonomous.credentials.intelligence.trend_analyzer import (
    IntelligenceTrendAnalyzer,
)


def test_trend():

    result = IntelligenceTrendAnalyzer().analyse(
        [
            {
                "confidence": 0.83
            },
            {
                "confidence": 0.55
            },
        ]
    )

    assert result["trend"] == "declining"
    assert result["mode"] == "read_only"
