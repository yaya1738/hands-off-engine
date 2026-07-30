from ai.factory.capability_assessment_runner import (
    FactoryCapabilityAssessmentRunner,
)


def test_assessment_runner():

    runner = FactoryCapabilityAssessmentRunner()

    result = runner.run_assessment(
        "runtime_foundation",
        [
            "factory_runtime",
            "event_bus",
            "improvement_cycle",
        ],
        [
            "factory_runtime",
            "event_bus",
            "improvement_cycle",
            "lifecycle_coordination",
        ],
        "identify missing runtime foundation capabilities",
    )

    assert result["status"] == "COMPLETE"
    assert result["evaluation"]["needs_evolution"] is True


def test_history():

    runner = FactoryCapabilityAssessmentRunner()

    runner.run_assessment(
        "test",
        ["a"],
        ["a", "b"],
        "test gap",
    )

    assert len(runner.history()) == 1
