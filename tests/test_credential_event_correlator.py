from autonomous.credentials.intelligence.event_correlator import (
    IntelligenceEventCorrelator,
)


def test_event_correlation():

    result = IntelligenceEventCorrelator().analyze(
        [
            {
                "event_type":
                "confidence_alert"
            },
            {
                "event_type":
                "confidence_alert"
            },
        ]
    )

    assert result["correlation"] == (
        "repeated_intelligence_signal"
    )
    assert result["mode"] == "read_only"
