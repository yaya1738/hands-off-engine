from ai.factory.improvement_prioritizer import (
    FactoryImprovementPrioritizer,
)


def test_prioritizes_foundation_gaps():

    prioritizer = FactoryImprovementPrioritizer()

    result = prioritizer.prioritize(
        [
            "runtime_health_monitoring",
            "lifecycle_coordination",
            "event_driven_orchestration",
        ]
    )

    assert result["ranked_improvements"][0] == (
        "lifecycle_coordination"
    )


def test_history():

    prioritizer = FactoryImprovementPrioritizer()

    prioritizer.prioritize(
        ["test_gap"]
    )

    assert len(prioritizer.history()) == 1
