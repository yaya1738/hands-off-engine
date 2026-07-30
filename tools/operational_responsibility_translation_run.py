import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.factory.development_entry_point import FactoryDevelopmentEntryPoint


def main():

    factory = FactoryDevelopmentEntryPoint()

    result = factory.submit_objective(
        "Improve context_to_responsibility_translation to generate operational engineering responsibilities from architecture context",

        [
            "context_to_responsibility_translation",
            "architecture_context_enrichment",
            "improvement_design_generator",
            "specification_development_bridge",
            "verification",
        ],

        [
            "operational_responsibility_generation",
            "behavior_definition",
            "interface_responsibility_mapping",
            "verification_responsibility_mapping",
        ],

        architecture_context={
            "interfaces": [
                "specification generator API",
                "architecture context API",
                "verification API",
            ],
            "integration_points": [
                "improvement_design_generator",
                "development_entry_point",
                "verification",
            ],
            "data_requirements": [
                "capability intent",
                "component context",
                "interfaces",
                "dependencies",
                "expected behavior",
            ],
            "verification_patterns": [
                "responsibility completeness checks",
                "behavior validation",
                "specification quality tests",
            ],
        },
    )

    print("OPERATIONAL RESPONSIBILITY TRANSLATION RUN")
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
