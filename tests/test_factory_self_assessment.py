from ai.factory.self_assessment import FactorySelfAssessment


def test_interaction_health_is_assessed_without_changing_execution_health():
    assessment = FactorySelfAssessment().assess(
        {
            "success_rate": 1.0,
            "average_impact": 0.5,
            "interaction_health": {
                "available": True,
                "interaction_correlation_rate": 0.5,
                "interaction_orphan_replies": 1,
                "interaction_unlinked_events": 1,
                "interaction_task_thread_coverage": 0.5,
                "interaction_window_truncated": True,
            },
        }
    )

    assert assessment["health"] == 1.0
    assert "low interaction correlation" in assessment["gaps"]
    assert "orphaned interaction replies" in assessment["gaps"]
    assert "truncated interaction observation window" in assessment["gaps"]
    assert assessment["interaction_health"]["interaction_task_thread_coverage"] == 0.5


def test_unavailable_interaction_health_does_not_create_gaps():
    assessment = FactorySelfAssessment().assess(
        {
            "success_rate": 1.0,
            "average_impact": 0.5,
            "interaction_health": {"available": False},
        }
    )

    assert assessment["health"] == 1.0
    assert assessment["gaps"] == []
