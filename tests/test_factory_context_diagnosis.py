from scripts.factory_context_diagnosis import diagnose_factory_context


def test_diagnoses_interaction_degradation_first():
    result = diagnose_factory_context({
        "interaction": {
            "available": True,
            "correlation_rate": 0.5,
            "orphan_reply_count": 1,
            "window_truncated": False,
        },
        "system_health": {"available": True, "status": "ok", "error_count": 0},
    })
    assert result == {
        "available": True,
        "diagnosis": "interaction_degradation",
        "observation_complete": True,
    }


def test_diagnoses_system_health_degradation():
    result = diagnose_factory_context({
        "interaction": {"available": True, "correlation_rate": 1.0},
        "system_health": {"available": True, "status": "warn", "error_count": 2},
    })
    assert result["diagnosis"] == "system_health_degradation"


def test_missing_observation_fails_closed_to_incomplete():
    result = diagnose_factory_context({"interaction": {"available": True}})
    assert result["diagnosis"] == "observation_incomplete"
    assert result["observation_complete"] is False


def test_healthy_context_is_explicit():
    result = diagnose_factory_context({
        "interaction": {"available": True, "correlation_rate": 1.0, "orphan_reply_count": 0},
        "system_health": {"available": True, "status": "ok", "error_count": 0, "recent_error_rate": 0.0},
    })
    assert result["diagnosis"] == "healthy"


def test_malformed_context_fails_closed():
    assert diagnose_factory_context(None) == {"available": False}
