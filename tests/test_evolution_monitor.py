from ai.factory.evolution_monitor import (
    FactoryEvolutionMonitor,
)


def test_detects_evolution_need():

    monitor = FactoryEvolutionMonitor()

    result = monitor.evaluate_state(
        [
            "gap_resolution",
            "component_design",
        ],
        [
            "gap_resolution",
            "component_design",
            "automatic_creation",
        ],
    )

    assert result["needs_evolution"] is True
    assert "automatic_creation" in result["missing_capabilities"]


def test_triggers_gap_request():

    monitor = FactoryEvolutionMonitor()

    result = monitor.trigger_gap_analysis(
        "creation_coordinator",
        "connect specifications to builders",
        [
            "accept specifications",
            "route creation",
            "track completion",
        ],
    )

    assert result["generated"] is True
