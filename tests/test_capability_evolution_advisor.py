from ai.factory.capability_evolution_advisor import (
    FactoryCapabilityEvolutionAdvisor,
)


def test_detects_missing_capability():

    advisor = FactoryCapabilityEvolutionAdvisor()

    result = advisor.evaluate_capabilities(
        [
            "gap_resolution",
            "component_design",
        ],
        [
            "gap_resolution",
            "component_design",
            "capability_routing",
        ],
    )

    assert result["needs_evolution"] is True


def test_generates_recommendation():

    advisor = FactoryCapabilityEvolutionAdvisor()

    result = advisor.generate_recommendation(
        "capability_design_router",
        "route design requests to correct process",
        [
            "classify need",
            "select design mechanism",
            "track result",
        ],
    )

    assert result["generated"] is True
