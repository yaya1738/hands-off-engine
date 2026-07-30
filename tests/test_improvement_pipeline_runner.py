from ai.factory.improvement_pipeline_runner import (
    FactoryImprovementPipelineRunner,
)


def test_full_improvement_pipeline():

    runner = FactoryImprovementPipelineRunner()

    result = runner.run(
        "runtime_foundation_test",
        [
            "factory_runtime",
            "event_bus",
        ],
        [
            "factory_runtime",
            "lifecycle_coordination",
        ],
        "identify next runtime foundation improvement",
    )

    assert result["status"] == "COMPLETE"

    assert (
        result["development_request"]["created"]
        is True
    )


def test_history():

    runner = FactoryImprovementPipelineRunner()

    runner.run(
        "test",
        ["a"],
        ["a", "b"],
        "test",
    )

    assert len(runner.history()) == 1
