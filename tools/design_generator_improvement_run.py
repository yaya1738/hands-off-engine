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
        "Improve FactoryImprovementDesignGenerator to create implementation-ready specifications",

        [
            "improvement_design_generator",
            "specification_development_bridge",
            "development_entry_point",
            "verification",
        ],

        [
            "implementation_ready_specifications",
            "interface_definition",
            "integration_mapping",
            "verification_criteria_generation",
            "architecture_context_awareness",
        ],
    )

    print("DESIGN GENERATOR IMPROVEMENT RUN")
    print("=" * 45)

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
