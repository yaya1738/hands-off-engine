from pathlib import Path
import json


INPUT = Path("factory_capability_analysis.json")
OUTPUT = Path("factory_capability_decisions.json")


def decide(analysis):
    decisions = []

    capabilities = analysis.get(
        "capabilities",
        {}
    )

    classifications = analysis.get(
        "classifications",
        []
    )

    for item in classifications:
        if item.get("type") == "multiple_implementations":
            decisions.append(
                {
                    "action": "review_duplicates",
                    "capability": item["capability"],
                    "reason": "multiple implementations detected",
                }
            )

    for name, data in capabilities.items():
        count = data.get("count", 0)

        if count == 1:
            decisions.append(
                {
                    "action": "reuse_existing",
                    "capability": name,
                    "reason": "single implementation detected",
                }
            )

        elif count > 1:
            decisions.append(
                {
                    "action": "evaluate_integration",
                    "capability": name,
                    "reason": "multiple possible providers detected",
                }
            )

    if not decisions:
        decisions.append(
            {
                "action": "no_action",
                "reason": "no capability decisions generated",
            }
        )

    return {
        "decisions": decisions,
        "decision_count": len(decisions),
    }


def main():
    analysis = json.loads(
        INPUT.read_text()
    )

    result = decide(
        analysis
    )

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        "Capability decision analysis complete"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
