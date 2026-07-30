import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.factory.improvement_pipeline_runner import (
    FactoryImprovementPipelineRunner,
)


def main():
    runner = FactoryImprovementPipelineRunner()

    result = runner.run(
        "factory_runtime_foundation",
        [
            "factory_runtime",
            "event_bus",
            "state",
            "execution",
            "decision",
            "planning",
            "learning",
            "audit",
            "improvement_cycle",
        ],
        [
            "factory_runtime",
            "lifecycle_coordination",
            "unified_bootstrap",
            "event_driven_orchestration",
            "state_management",
            "capability_registry",
            "runtime_health_monitoring",
        ],
        "identify and prepare the highest priority runtime foundation improvement",
    )

    print("RUNTIME IMPROVEMENT PIPELINE RESULT")
    print("=" * 45)

    print("\nSTATUS:")
    print(result["status"])

    print("\nROADMAP:")
    print(
        result["roadmap"]["roadmap"]
    )

    print("\nSPECIFICATION:")
    print(
        result["specification"]["specification"]
    )

    print("\nDEVELOPMENT REQUEST:")
    print(
        result["development_request"]["request"]
    )


if __name__ == "__main__":
    main()
