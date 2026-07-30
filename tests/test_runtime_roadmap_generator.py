from ai.factory.runtime_roadmap_generator import (
    FactoryRuntimeRoadmapGenerator,
)


def test_generates_runtime_roadmap():

    generator = FactoryRuntimeRoadmapGenerator()

    report = {
        "assessment": "runtime_foundation",
        "gaps": {
            "gap": {
                "missing_capabilities": [
                    "runtime_health_monitoring",
                    "lifecycle_coordination",
                    "event_driven_orchestration",
                ]
            }
        },
    }

    result = generator.generate(report)

    assert result["status"] == "GENERATED"
    assert result["roadmap"]["ranked_improvements"][0] == (
        "lifecycle_coordination"
    )


def test_history():

    generator = FactoryRuntimeRoadmapGenerator()

    generator.generate({
        "gaps": {
            "gap": {
                "missing_capabilities": [
                    "test_gap"
                ]
            }
        }
    })

    assert len(generator.history()) == 1
