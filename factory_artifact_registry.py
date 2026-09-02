"""Read-only artifact registry compatibility facade.

Legacy classifier process execution and registry persistence are disabled.
Operational artifact classification must be routed through FactoryAuthorityGateway.
"""

import json


REGISTRY_FILE = "factory_artifact_registry.json"

CLASS_MAP = {
    "historical_analysis_artifact": "evidence",
    "next_phase_candidate": "active_phase_asset",
    "control_tool": "factory_tool",
    "unknown": "unclassified",
}


def run_classifier():
    """Compatibility boundary: do not launch the legacy classifier."""
    return {
        "authority_required": True,
        "message": "[FACTORY-AUTHORITY] Legacy artifact classifier execution is disabled; use FactoryAuthorityGateway.",
        "artifacts": [],
    }


def build_registry():
    classified = run_classifier()
    return {
        "artifacts": classified.get("artifacts", []),
        "summary": {
            "evidence": 0,
            "active_phase_asset": 0,
            "factory_tool": 0,
            "unclassified": 0,
        },
        "authority_required": True,
        "message": classified["message"],
    }


def main():
    registry = build_registry()
    print(json.dumps(registry, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
