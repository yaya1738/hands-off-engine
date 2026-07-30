from ai.factory.improvement_design_generator import (
    FactoryImprovementDesignGenerator,
)


def test_responsibility_generation_creates_specific_engineering_duties():

    generator = FactoryImprovementDesignGenerator()

    result = generator.generate_specification(
        "responsibility_generation_engine",
        "Create capability for specification synthesis",
        [],
        [
            "FactoryRuntime",
            "DevelopmentPipeline",
        ],
        problem="Improve specification quality and engineering responsibility mapping",
        data_requirements=[
            "objective meaning",
            "interfaces",
            "dependencies",
        ],
        verification_criteria=[
            "quality validation",
        ],
    )

    responsibilities = result["specification"]["responsibilities"]

    assert "translate capability intent into engineering duties" in responsibilities
    assert "define operational component responsibilities" in responsibilities
    assert "define verification obligations" in responsibilities
