import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.factory.development_entry_point import FactoryDevelopmentEntryPoint


def main():

    factory = FactoryDevelopmentEntryPoint()

    result = factory.submit_objective(
        "Create Responsibility Generation Engine capability for specification synthesis",

        [
            "context_to_responsibility_translation",
            "architecture_context_enrichment",
            "improvement_design_generator",
            "specification_development_bridge",
            "verification",
        ],

        [
            "responsibility_generation_engine",
            "operational_responsibility_mapping",
            "implementation_ready_specifications",
            "responsibility_quality_validation",
        ],

        architecture_context={
            "interfaces": [
                "specification generator API",
                "architecture context API",
                "verification API",
            ],
            "integration_points": [
                "FactoryRuntime",
                "ImprovementPipeline",
                "DevelopmentPipeline",
            ],
            "data_requirements": [
                "objective meaning",
                "capability purpose",
                "interfaces",
                "dependencies",
                "integration points",
                "verification criteria",
            ],
            "verification_patterns": [
                "responsibility completeness checks",
                "specification quality validation",
                "pipeline verification",
            ],
        },
    )

    print("RESPONSIBILITY GENERATION ENGINE DESIGN RUN")
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
