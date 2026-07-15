from autonomous.credentials.intelligence.temporal import (
    CredentialTemporalAnalyzer,
)


def test_temporal_analysis():

    events = [
        {
            "timestamp":
            "2026-07-14T10:00:00+00:00"
        },
        {
            "timestamp":
            "2026-07-14T10:10:00+00:00"
        },
    ]

    result = CredentialTemporalAnalyzer().analyze(events)

    assert result["event_count"] == 2
    assert result["observed_window_seconds"] == 600
