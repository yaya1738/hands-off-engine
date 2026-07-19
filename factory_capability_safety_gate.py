from pathlib import Path
import json


INPUT = Path("factory_capability_integration_plan.json")
OUTPUT = Path("factory_capability_execution_request.json")


def assess(plan):
    requests = []

    for item in plan.get("plans", []):
        capability = item.get("capability")
        next_step = item.get("next_step", "")

        risk = "low"

        if "consolidation" in next_step:
            risk = "high"

        elif "select integration target" in next_step:
            risk = "medium"

        requests.append(
            {
                "capability": capability,
                "planned_action": item.get("plan"),
                "next_step": next_step,
                "risk": risk,
                "status": (
                    "approved_for_automation"
                    if risk == "low"
                    else "requires_review"
                ),
            }
        )

    return {
        "execution_requests": requests,
        "count": len(requests),
    }


def main():
    plan = json.loads(
        INPUT.read_text()
    )

    result = assess(plan)

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print("Safety gate complete")
    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
