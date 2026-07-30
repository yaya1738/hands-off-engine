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
        "Improve responsibility synthesis so generated specifications contain implementation-ready engineering responsibilities",

        [
            "improvement_design_generator",
            "architecture_context_enrichment",
            "capability_assessment",
            "specification_development_bridge",
            "verification",
        ],

        [
            "responsibility_pattern_generation",
            "capability_type_reasoning",
            "implementation_ready_specifications",
            "design_quality_improvement",
        ],

        architecture_context={
            "interfaces": [
                "specification generator API",
                "capability assessment API",
            ],
            "integration_points": [
                "improvement_design_generator",
                "development_entry_point",
            ],
            "data_requirements": [
                "objective meaning",
                "capability category",
                "architecture context",
                "existing responsibilities",
            ],
            "verification_patterns": [
                "specification quality tests",
                "responsibility accuracy checks",
                "pipeline validation",
            ],
        },
    )

    print("RESPONSIBILITY SYNTHESIS ASSESSMENT")
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
