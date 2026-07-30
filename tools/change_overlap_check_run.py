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
        "Create development change overlap checking capability",

        [
            "capability_assessment",
            "improvement_prioritizer",
            "architecture_context_enrichment",
            "improvement_design_generator",
            "development_entry_point",
            "verification",
        ],

        [
            "capability_overlap_detection",
            "duplicate_component_prevention",
            "existing_component_matching",
            "extension_vs_creation_decision",
        ],

        architecture_context={
            "interfaces": [
                "capability registry API",
                "component metadata API",
                "development request API",
            ],
            "integration_points": [
                "development_entry_point",
                "specification_development_bridge",
                "capability_assessment",
            ],
            "data_requirements": [
                "existing components",
                "capability history",
                "dependency relationships",
            ],
            "verification_patterns": [
                "duplicate detection tests",
                "integration tests",
                "decision validation tests",
            ],
        },
    )

    print("CHANGE OVERLAP CHECK DESIGN RUN")
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
