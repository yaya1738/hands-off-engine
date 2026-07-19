from pathlib import Path
import json


INPUT = Path("factory_capability_decisions.json")
OUTPUT = Path("factory_capability_integration_plan.json")


def build_plan(data):
    plan = {
        "plans": [],
        "summary": {
            "reuse": 0,
            "integration": 0,
            "review": 0,
            "new_capability": 0,
        },
    }

    for decision in data.get("decisions", []):
        action = decision.get("action")
        capability = decision.get("capability")

        if action == "reuse_existing":
            plan["plans"].append(
                {
                    "capability": capability,
                    "plan": "reuse existing capability",
                    "next_step": "connect consumer to provider",
                }
            )
            plan["summary"]["reuse"] += 1

        elif action == "evaluate_integration":
            plan["plans"].append(
                {
                    "capability": capability,
                    "plan": "evaluate existing implementations",
                    "next_step": "select integration target",
                }
            )
            plan["summary"]["integration"] += 1

        elif action == "review_duplicates":
            plan["plans"].append(
                {
                    "capability": capability,
                    "plan": "review duplicate implementations",
                    "next_step": "consolidation analysis",
                }
            )
            plan["summary"]["review"] += 1

        else:
            plan["plans"].append(
                {
                    "capability": capability,
                    "plan": "investigate capability gap",
                    "next_step": "create capability request",
                }
            )
            plan["summary"]["new_capability"] += 1

    return plan


def main():
    data = json.loads(
        INPUT.read_text()
    )

    result = build_plan(data)

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        "Integration planning complete"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
