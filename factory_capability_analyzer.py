from pathlib import Path
import json


REPORT = Path("factory_capability_report.json")
OUTPUT = Path("factory_capability_analysis.json")


RULES = {
    "diagnostic": "diagnostic capability detected",
    "inspect": "inspection capability detected",
    "audit": "audit capability detected",
    "registry": "registry capability detected",
    "dependency": "dependency capability detected",
    "graph": "graph capability detected",
    "runtime": "runtime capability detected",
    "health": "health capability detected",
    "executor": "execution capability detected",
    "scheduler": "scheduling capability detected",
}


def load_report():
    return json.loads(
        REPORT.read_text()
    )


def analyze(data):
    capabilities = data.get(
        "summary",
        {}
    ).get(
        "capabilities_found",
        {}
    )

    analysis = {
        "capabilities": {},
        "classifications": [],
        "recommendations": [],
    }

    for key, files in capabilities.items():
        analysis["capabilities"][key] = {
            "count": len(files),
            "files": files,
        }

        if len(files) > 1:
            analysis["classifications"].append(
                {
                    "type": "multiple_implementations",
                    "capability": key,
                    "count": len(files),
                }
            )

    for capability, description in RULES.items():
        if capability in capabilities:
            analysis["recommendations"].append(
                {
                    "capability": capability,
                    "status": "present",
                    "note": description,
                }
            )

    return analysis


def main():
    data = load_report()

    result = analyze(data)

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        "Capability analysis complete"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
