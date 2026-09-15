from ai.factory.assessment_observability import FactoryAssessmentObservability


def test_assessment_snapshot_is_bounded_and_read_only():
    assessment = {
        "health": 1.0,
        "gaps": ["orphaned interaction replies"],
        "objective": "observe",
        "context": "internal",
        "interaction_health": {
            "available": True,
            "interaction_correlation_rate": 0.5,
            "interaction_orphan_replies": 1,
            "interaction_window_truncated": False,
        },
        "secret": "must-not-leak",
    }

    snapshot = FactoryAssessmentObservability().snapshot(assessment)

    assert snapshot == {
        "available": True,
        "health": 1.0,
        "gaps": ["orphaned interaction replies"],
        "objective": "observe",
        "interaction_health": {
            "available": True,
            "interaction_correlation_rate": 0.5,
            "interaction_orphan_replies": 1,
            "interaction_window_truncated": False,
        },
    }
    assert "secret" not in snapshot
    assert assessment["gaps"] == ["orphaned interaction replies"]
