from pathlib import Path
import json
import subprocess


REGISTRY_FILE = Path("factory_artifact_registry.json")


CLASS_MAP = {
    "historical_analysis_artifact": "evidence",
    "next_phase_candidate": "active_phase_asset",
    "control_tool": "factory_tool",
    "unknown": "unclassified",
}


def run_classifier():
    output = subprocess.check_output(
        ["python", "factory_workspace_artifact_classifier.py"],
        text=True,
    )

    return json.loads(output)


def build_registry():
    classified = run_classifier()

    registry = {
        "artifacts": [],
        "summary": {
            "evidence": 0,
            "active_phase_asset": 0,
            "factory_tool": 0,
            "unclassified": 0,
        },
    }

    for item in classified["artifacts"]:
        category = CLASS_MAP.get(
            item["classification"],
            "unclassified",
        )

        record = {
            "file": item["file"],
            "classifier_result": item["classification"],
            "registry_category": category,
        }

        registry["artifacts"].append(record)
        registry["summary"][category] += 1

    return registry


def main():
    registry = build_registry()

    REGISTRY_FILE.write_text(
        json.dumps(
            registry,
            indent=2,
        )
    )

    print(
        json.dumps(
            registry,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
