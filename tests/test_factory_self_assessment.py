from ai.factory.self_assessment import FactorySelfAssessment


class StubInteractionObserver:
    def __init__(self, health):
        self.health = health
        self.calls = 0

    def observe(self):
        self.calls += 1
        return self.health


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


def test_self_assessment_observes_interaction_health_when_not_supplied():
    observer = StubInteractionObserver(
        {
            "available": True,
            "interaction_correlation_rate": 0.5,
            "interaction_orphan_replies": 1,
            "interaction_unlinked_events": 0,
            "interaction_task_thread_coverage": 1.0,
            "interaction_window_truncated": False,
        }
    )

    assessment = FactorySelfAssessment(
        interaction_observer=observer,
    ).assess(
        {
            "success_rate": 1.0,
            "average_impact": 0.5,
        }
    )

    assert observer.calls == 1
    assert assessment["health"] == 1.0
    assert "low interaction correlation" in assessment["gaps"]
    assert "orphaned interaction replies" in assessment["gaps"]
    assert assessment["interaction_health"]["interaction_task_thread_coverage"] == 1.0


def test_supplied_interaction_health_is_not_reobserved():
    observer = StubInteractionObserver({"available": False})

    assessment = FactorySelfAssessment(
        interaction_observer=observer,
    ).assess(
        {
            "success_rate": 1.0,
            "average_impact": 0.5,
            "interaction_health": {"available": True},
        }
    )

    assert observer.calls == 0
    assert assessment["interaction_health"]["available"] is True
