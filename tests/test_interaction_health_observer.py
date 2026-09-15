from pathlib import Path

from ai.factory.interaction_health_observer import FactoryInteractionHealthObserver


def test_factory_interaction_health_observer_is_read_only_and_machine_facing(
    tmp_path: Path,
    monkeypatch,
):
    health = {
        "available": True,
        "correlated_event_count": 8,
        "orphan_reply_count": 1,
        "single_event_count": 1,
        "explicit_task_thread_coverage": 0.75,
        "window": {"truncated": True},
    }

    monkeypatch.setattr(
        "ai.factory.interaction_health_observer.read_interaction_health",
        lambda repo_root=None, bus_limit=120: health,
    )

    before = dict(health)
    result = FactoryInteractionHealthObserver().observe(tmp_path, bus_limit=10)

    assert result["available"] is True
    assert result["interaction_correlation_rate"] == 0.8
    assert result["interaction_orphan_replies"] == 1
    assert result["interaction_unlinked_events"] == 1
    assert result["interaction_task_thread_coverage"] == 0.75
    assert result["interaction_window_truncated"] is True
    assert result["interaction_health"] == before
