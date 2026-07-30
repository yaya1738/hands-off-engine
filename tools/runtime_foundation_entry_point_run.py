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
        "Improve Factory runtime foundation",

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
            "capability_registry",
            "event_driven_orchestration",
            "runtime_health_monitoring",
        ],
    )

    print("FACTORY DEVELOPMENT ENTRY POINT RUN")
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
