import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.factory.capability_assessment_runner import (
    FactoryCapabilityAssessmentRunner,
)


def main():
    runner = FactoryCapabilityAssessmentRunner()

    report = runner.run_assessment(
        "factory_runtime_foundation",
        [
            "factory_runtime",
            "event_bus",
            "state",
            "execution",
            "improvement_cycle",
            "audit",
            "decision",
            "planning",
            "learning",
        ],
        [
            "factory_runtime",
            "lifecycle_coordination",
            "unified_bootstrap",
            "event_driven_orchestration",
            "state_management",
            "improvement_cycle",
            "capability_registry",
            "runtime_health_monitoring",
        ],
        "evaluate runtime foundation readiness and identify missing coordination layers",
    )

    print("RUNTIME FOUNDATION ASSESSMENT")
    print("=" * 40)

    print("\nSTATUS:")
    print(report["status"])

    print("\nOBJECTIVE:")
    print(report["objective"])

    print("\nEVOLUTION:")
    print(report["evaluation"])

    print("\nGAPS:")
    print(report["gaps"])


if __name__ == "__main__":
    main()
