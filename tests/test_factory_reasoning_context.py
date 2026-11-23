from scripts.factory_reasoning_context import build_factory_reasoning_context


def test_reasoning_context_contains_only_bounded_observation_fields():
    result = build_factory_reasoning_context({
        "interaction": {"available": True, "correlation_rate": 0.9},
        "system_health": {"available": True, "status": "ok", "error_count": 0},
        "admission": {"available": True, "msg_id": "m-1", "task_id": "t-1", "admitted": True},
        "authority": {"available": True, "msg_id": "m-1", "decision": "approved", "execution_enabled": True},
        "assessment": {"available": True, "health": 0.9, "gaps": []},
        "secret": "must-not-leak",
    })
    assert result["available"] is True
    assert result["diagnosis"] == "healthy"
    assert result["authority"]["decision"] == "approved"
    assert "execution_enabled" not in result["authority"]
    assert "secret" not in result


def test_reasoning_context_does_not_expose_execution_capability():
    result = build_factory_reasoning_context({
        "interaction": {"available": True, "correlation_rate": 1.0},
        "system_health": {"available": True, "status": "ok", "error_count": 0},
        "authority": {"available": True, "decision": "approved", "execution_enabled": True},
    })
    assert result["authority"]["decision"] == "approved"
    assert "execution_enabled" not in result["authority"]


def test_reasoning_context_preserves_incomplete_diagnosis():
    result = build_factory_reasoning_context({"interaction": {"available": True}})
    assert result["available"] is True
    assert result["diagnosis"] == "observation_incomplete"
    assert result["observation_complete"] is False


def test_malformed_context_fails_closed():
    assert build_factory_reasoning_context(None) == {"available": False}
