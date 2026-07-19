from pathlib import Path
import json
from datetime import datetime, timezone


OUTPUT = Path("factory_workflow_patterns.json")


DEFAULT_PATTERNS = [
    {
        "name": "discovery_to_integration",
        "purpose": "Find existing capability before creating new capability",
        "tools": [
            "factory_artifact_registry",
            "factory_capability_analyzer",
            "factory_capability_decision_engine",
            "factory_capability_integration_planner",
            "factory_capability_safety_gate",
        ],
        "success_conditions": [
            "existing capability found",
            "integration plan produced",
            "safety gate passed",
        ],
    },
    {
        "name": "runtime_repair",
        "purpose": "Diagnose and repair runtime contract problems",
        "tools": [
            "constructor_contract_analyzer",
            "dependency_usage_audit",
            "repair_assistant",
            "checkpoint_validator",
        ],
        "success_conditions": [
            "contract mismatch identified",
            "repair validated",
            "checkpoint created",
        ],
    },
    {
        "name": "phase_transition",
        "purpose": "Secure boundaries before moving phases",
        "tools": [
            "factory_milestone_gate",
            "factory_phase_transition_gate",
            "artifact_registry",
        ],
        "success_conditions": [
            "milestone exists",
            "workspace boundary clean",
            "next phase approved",
        ],
    },
]


def build_registry():
    registry = {
        "generated": datetime.now(
            timezone.utc
        ).isoformat(),
        "patterns": DEFAULT_PATTERNS,
    }

    OUTPUT.write_text(
        json.dumps(
            registry,
            indent=2,
        )
    )

    return registry


if __name__ == "__main__":
    print(
        json.dumps(
            build_registry(),
            indent=2,
        )
    )
