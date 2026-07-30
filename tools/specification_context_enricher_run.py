import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.factory.development_entry_point import (
    FactoryDevelopmentEntryPoint,
)


def main():
    factory = FactoryDevelopmentEntryPoint()

    result = factory.submit_objective(
        "Create Specification Context Enrichment capability",

        [
            "capability_assessment",
            "improvement_prioritizer",
            "roadmap_generator",
            "improvement_design_generator",
            "specification_development_bridge",
            "development_entry_point",
            "verification",
        ],

        [
            "architecture_context_enrichment",
            "existing_component_mapping",
            "dependency_discovery",
            "runtime_integration_mapping",
            "verification_pattern_generation",
            "implementation_ready_specifications",
        ],

        architecture_context={
            "interfaces": [
                "Factory runtime API",
                "development pipeline API",
                "event interface",
            ],
            "integration_points": [
                "FactoryRuntime",
                "ImprovementPipeline",
                "DevelopmentPipeline",
            ],
            "data_requirements": [
                "component registry",
                "dependency map",
                "runtime state",
            ],
            "verification_patterns": [
                "unit tests",
                "integration tests",
                "pipeline validation",
            ],
        },
    )

    print("SPECIFICATION CONTEXT ENRICHER DESIGN RUN")
    print("=" * 50)

    print("\nSTATUS:")
    print(result["status"])

    print("\nROADMAP:")
    print(result["roadmap"]["roadmap"])

    print("\nSPECIFICATION:")
    print(result["specification"]["specification"])

    print("\nDEVELOPMENT REQUEST:")
    print(result["development_request"]["request"])


if __name__ == "__main__":
    main()
