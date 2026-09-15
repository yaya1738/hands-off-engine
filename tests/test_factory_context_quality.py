from scripts.factory_context_quality import summarize_context_quality


def test_context_quality_identifies_observation_gaps():
    result = summarize_context_quality({
        "interaction": {"available": True, "window_truncated": True},
        "system_health": {"available": True, "error_count": 2},
    })
    assert result["available"] is True
    assert result["complete"] is False
    assert "interaction observation window truncated" in result["gaps"]
    assert "system health reports recent errors" in result["gaps"]


def test_missing_context_fails_closed():
    assert summarize_context_quality(None) == {"available": False}
