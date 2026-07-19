from pathlib import Path
import json


FILES = [
    Path(x)
    for x in Path(".").iterdir()
    if x.name.startswith("factory_")
    and x.name not in [
        "factory_runtime_checkpoint.json"
    ]
]


def classify(path):
    name = path.name

    if any(x in name for x in [
        "discovery",
        "audit",
        "analysis",
        "signature",
        "unified_report",
    ]):
        return "historical_analysis_artifact"

    if any(x in name for x in [
        "autonomy",
        "capability",
        "execution",
        "validation",
    ]):
        return "next_phase_candidate"

    if "gate" in name:
        return "control_tool"

    return "unknown"


def main():
    result = {
        "artifacts": []
    }

    for file in FILES:
        result["artifacts"].append(
            {
                "file": str(file),
                "classification": classify(file),
            }
        )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
