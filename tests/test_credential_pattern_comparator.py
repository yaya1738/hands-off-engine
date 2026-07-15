from autonomous.credentials.intelligence.pattern_comparator import (
    IntelligencePatternComparator,
)


def test_compare():

    result = IntelligencePatternComparator().compare(
        {
            "pattern_id": "repeated_high_risk_attention",
            "occurrences": 1,
        },
        {
            "pattern_id": "repeated_high_risk_attention",
            "occurrences": 2,
        },
    )

    assert result["comparison"] == "pattern_repeated"
    assert result["trend"] == "persistent"
    assert result["mode"] == "read_only"
